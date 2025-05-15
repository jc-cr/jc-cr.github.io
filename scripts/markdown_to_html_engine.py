# update_posts.py
import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
import markdown
import urllib.parse
from dotenv import load_dotenv

class PostGenerator:
    def __init__(self, base_dir: str = None):
        # Load environment variables
        load_dotenv()
        
        # Use provided base_dir or determine based on environment
        self.base_dir = Path(base_dir if base_dir else '/app')
        
        # Get the actual post path from environment
        post_path_env = os.getenv('POST_PATH', '')
        # If it's a real path that exists, use it directly
        if post_path_env and Path(post_path_env).exists():
            self.post_path = Path(post_path_env)
        else:
            # Fall back to the default Docker path for backward compatibility
            self.post_path = Path('/input/post.md')
            
        # Set up other paths
        self.obsidian_path = Path('/input/obsidian')
        self.output_dir = self.base_dir / 'webpage'
        self.template_dir = self.base_dir / 'templates'
        self.indexes_dir = self.output_dir / 'indexes'
        
        # Initialize templates
        self.post_template = self.template_dir / 'post_template.html'
        self.index_template = self.template_dir / 'index_template.html'
        self.section_template = self.template_dir / 'section_template.html'
        
        # Clean configuration from env
        self.post_type = os.getenv('POST_TYPE', '').strip().strip('"\'')
        self.post_title = os.getenv('POST_TITLE', '').strip().strip('"\'')
        self.post_date = os.getenv('POST_DATE', '').strip().strip('"\'') or datetime.now().strftime('%Y-%m-%d')
        
        # Get tags from environment
        self.post_tags = os.getenv('POST_TAGS', '').strip().strip('"\'').split(',')
        # Filter out empty strings from the tags list
        self.post_tags = [tag for tag in self.post_tags if tag]
        # If no tags were specified but post_type is set, use that as a default tag
        if not self.post_tags and self.post_type:
            self.post_tags = [self.post_type]
        
        # Create necessary directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate environment after setup
        self._validate_environment()

    def _validate_environment(self):
        """Validate all required paths and configuration"""
        if not self.obsidian_path.exists():
            raise FileNotFoundError(f"Obsidian vault not mounted at: {self.obsidian_path}")
            
        if not self.post_path.exists():
            raise FileNotFoundError(f"Markdown file not found at: {self.post_path}")
            
        if not self.post_path.is_file():
            raise ValueError(f"Post path exists but is not a file: {self.post_path}")
            
        try:
            with open(self.post_path, 'r') as f:
                f.read(1)  # Try to read one byte to verify file is readable
        except Exception as e:
            raise IOError(f"Cannot read post file at {self.post_path}: {e}")

        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
            
        if not self.post_template.exists():
            raise FileNotFoundError(f"Template not found: {self.post_template}")
            
        if not self.post_type:
            raise ValueError("POST_TYPE must be set in environment")
            
        if not self.post_title and self.post_path:
            self.post_title = self.post_path.stem

    def _find_image(self, filename: str) -> Path:
        """Find image in mounted Obsidian vault"""
        filename = filename.strip()
        
        # Try direct path first
        direct_path = self.obsidian_path / filename
        if direct_path.exists() and direct_path.is_file():
            return direct_path
            
        # Search for file recursively
        try:
            pattern = filename.lower()
            for file_path in self.obsidian_path.rglob('*'):
                if file_path.is_file() and file_path.name.lower() == pattern:
                    return file_path
        except Exception as e:
            print(f"Warning: Error searching for image {filename}: {e}")
            
        return None

    def _process_wikilinks(self, content: str, post_dir: Path) -> str:
        """Process Obsidian wikilinks and copy referenced files"""
        wikilink_pattern = r'!\[\[(.*?)\]\]'
        
        def process_wikilink(match):
            filename = match.group(1).strip()
            file_path = self._find_image(filename)
            
            if file_path and file_path.is_file():
                new_name = file_path.name
                new_path = post_dir / new_name
                shutil.copy2(file_path, new_path)
                encoded_name = urllib.parse.quote(new_name)
                
                # Check file extension to determine if it's a video
                extension = file_path.suffix.lower()
                video_extensions = {'.mp4', '.webm', '.ogg', '.mov'}
                
                if extension in video_extensions:
                    return f'''<figure>
        <video controls>
            <source src="{encoded_name}" type="video/{extension[1:]}" />
            Your browser does not support the video tag.
        </video>
    </figure>'''
                else:
                    return f'''<figure>
        <img src="{encoded_name}" alt="{new_name}" />
    </figure>'''
            
            print(f"Warning: File not found: {filename}")
            return f'[File not found: {filename}]'
        
        return re.sub(wikilink_pattern, process_wikilink, content)
    
    def _replace_template_vars(self, template: str, variables: dict) -> str:
        """Replace all template variables with their values"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{ {key} }}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def _extract_snippet(self, content, length=150):
        """Extract a snippet from the content with the specified length"""
        # Remove Markdown formatting and strip whitespace
        text_only = re.sub(r'!\[\[.*?\]\]', '', content)  # Remove wikilinks
        text_only = re.sub(r'#+\s', '', text_only)  # Remove headings
        text_only = re.sub(r'\*\*(.*?)\*\*', r'\1', text_only)  # Remove bold
        text_only = re.sub(r'\*(.*?)\*', r'\1', text_only)  # Remove italic
        text_only = re.sub(r'~~(.*?)~~', r'\1', text_only)  # Remove strikethrough
        text_only = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text_only)  # Remove links
        text_only = re.sub(r'`(.*?)`', r'\1', text_only)  # Remove code
        
        # Get first 150 characters
        snippet = ' '.join(text_only.split())  # Normalize whitespace
        if len(snippet) > length:
            # Try to end at a word boundary
            snippet = snippet[:length].rsplit(' ', 1)[0] + '...'
        
        return snippet

    def _create_post_directory(self) -> tuple[str, Path]:
        """Create directory for post based on title and date"""
        date_str = datetime.strptime(self.post_date, '%Y-%m-%d').strftime('%Y%m%d')
        
        # Create URL-safe slug from title
        slug = self.post_title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '_', slug)
        
        dir_name = f"{date_str}_{slug}"
        
        # Create directory in output_dir
        post_dir = self.output_dir / 'posts' / dir_name
        post_dir.mkdir(parents=True, exist_ok=True)
        
        return dir_name, post_dir

    def _create_meta_json(self, post_dir: Path, content: str):
        """Create meta.json file in the post directory"""
        snippet = self._extract_snippet(content)
        
        meta_data = {
            "title": self.post_title,
            "date": self.post_date,
            "tags": self.post_tags,
            "snippet": snippet
        }
        
        meta_file = post_dir / "meta.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, indent=2)

    def generate(self):
        """Generate all required files"""
        try:
            # Read markdown content
            with open(self.post_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create post directory
            dir_name, post_dir = self._create_post_directory()
            
            # Create meta.json file
            self._create_meta_json(post_dir, content)
            
            # Process content
            content = self._process_wikilinks(content, post_dir)
            html_content = markdown.markdown(
                content,
                extensions=['extra', 'meta', 'fenced_code', 'nl2br', 'sane_lists']
            )
            
            # Generate post HTML
            with open(self.post_template, 'r', encoding='utf-8') as f:
                template = f.read()
            
            post_vars = {
                'title': self.post_title,
                'content': html_content,
                'date': self.post_date,
                'tags': ', '.join(self.post_tags)  # Join the tags with commas
            }
            
            post_html = self._replace_template_vars(template, post_vars)
            
            # Write post HTML
            output_file = post_dir / 'post.html'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(post_html)
            
            print(f"Post generated successfully in {post_dir}")
            return str(post_dir)
            
        except Exception as e:
            print(f"Error generating post: {e}")
            raise

if __name__ == '__main__':
    try:
        generator = PostGenerator()
        generator.generate()
    except Exception as e:
        print(f"Error generating post: {e}")
        exit(1)