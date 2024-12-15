# update_posts.py
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
import markdown
import urllib.parse
from dotenv import load_dotenv
from registry_updater import PostRegistry

class PostGenerator:
    def __init__(self, base_dir: str = None):
        # Load environment variables
        load_dotenv()
        
        # Use provided base_dir or determine based on environment
        self.base_dir = Path(base_dir) if base_dir else self._get_base_dir()
        
        # Set up paths
        if self._is_docker():
            # Docker container paths
            self.obsidian_path = Path('/input/obsidian')
            self.post_path = Path('/input/post.md')
            self.output_dir = Path('/app/webpage')
            self.template_dir = Path('/app/templates')
            self.registry = PostRegistry('/app/data/posts.db')
        else:
            # Local/GitHub Actions paths
            self.obsidian_path = Path(os.getenv('OBSIDIAN_PATH', '')) if os.getenv('OBSIDIAN_PATH') else None
            self.post_path = Path(os.getenv('POST_PATH', '')) if os.getenv('POST_PATH') else None
            self.output_dir = self.base_dir / 'webpage'
            self.template_dir = self.base_dir / 'templates'
            self.registry = PostRegistry(str(self.base_dir / 'data' / 'posts.db'))
        
        # Initialize templates
        self.post_template = self.template_dir / 'post_template.html'
        self.index_template = self.template_dir / 'index_template.html'
        self.section_template = self.template_dir / 'section_template.html'
        
        # Clean configuration from env
        self.post_type = os.getenv('POST_TYPE', '').strip().strip('"\'')
        self.post_title = os.getenv('POST_TITLE', '').strip().strip('"\'')
        self.post_date = os.getenv('POST_DATE', '').strip().strip('"\'') or datetime.now().strftime('%Y-%m-%d')
        
        # Create necessary directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self._is_docker():
            (self.base_dir / 'data').mkdir(parents=True, exist_ok=True)

    def _is_docker(self) -> bool:
        """Check if running in Docker container"""
        return os.path.exists('/.dockerenv')

    def _get_base_dir(self) -> Path:
        """Get base directory based on environment"""
        if self._is_docker():
            return Path('/app')
        return Path.cwd()

    def _validate_environment(self):
        """Validate all required paths and configuration"""
        if self._is_docker():
            if not self.obsidian_path.exists():
                raise FileNotFoundError(f"Obsidian vault not found at container path: {self.obsidian_path}")
            
            if not self.post_path.exists():
                raise FileNotFoundError(f"Markdown file not found at container path: {self.post_path}")

        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
            
        if not self.post_template.exists():
            raise FileNotFoundError(f"Template not found: {self.post_template}")
            
        if not self.post_type:
            raise ValueError("POST_TYPE must be set in .env")
            
        if not self.post_title and self.post_path:
            self.post_title = self.post_path.stem

    def _find_image(self, filename: str) -> Path:
        """Find image in mounted Obsidian vault"""
        filename = filename.strip()
        
        direct_path = self.obsidian_path / filename
        if direct_path.exists():
            return direct_path
            
        try:
            pattern = filename.lower()
            for file_path in self.obsidian_path.rglob('*'):
                if file_path.name.lower() == pattern:
                    return file_path
        except Exception as e:
            print(f"Warning: Error searching for image {filename}: {e}")
            
        return None
    
    def _create_post_directory(self) -> Path:
        """Create directory for post based on title and date"""
        date_str = datetime.strptime(self.post_date, '%Y-%m-%d').strftime('%Y%m%d')
        
        slug = self.post_title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '_', slug)
        
        dir_name = f"{date_str}_{slug}"
        
        post_dir = self.output_dir / self.post_type / dir_name
        post_dir.mkdir(parents=True, exist_ok=True)
        
        return dir_name, post_dir
    
    def _process_wikilinks(self, content: str, post_dir: Path) -> str:
        """Process Obsidian wikilinks and copy referenced files"""
        wikilink_pattern = r'!\[\[(.*?)\]\]'
        
        def process_wikilink(match):
            filename = match.group(1).strip()
            image_path = self._find_image(filename)
            
            if image_path and image_path.exists():
                new_name = image_path.name
                new_path = post_dir / new_name
                shutil.copy2(image_path, new_path)
                encoded_name = urllib.parse.quote(new_name)
                
                return f'''<figure>
    <img src="{encoded_name}" alt="{new_name}" />
</figure>'''
            
            print(f"Warning: Image not found: {filename}")
            return f'[Image not found: {filename}]'
        
        return re.sub(wikilink_pattern, process_wikilink, content)
    
    def _replace_template_vars(self, template: str, variables: dict) -> str:
        """Replace all template variables with their values"""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{ {key} }}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def _generate_index_html(self):
        """Generate main index.html with latest posts"""
        with open(self.index_template, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Get latest posts from registry
        latest_posts = self.registry.get_latest_posts(5)
        
        # Generate latest posts HTML
        posts_html = ''
        for post in latest_posts:
            post_url = f"/webpage/{post['type']}/{post['path']}/post.html"
            posts_html += f'<li><a href="{post_url}">{post["title"]}</a> ({post["date"]})</li>\n'
        
        # Replace template variables
        variables = {
            'latest_posts': posts_html
        }
        index_html = self._replace_template_vars(template, variables)
        
        # Write to root directory
        index_path = self.base_dir / 'index.html'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
    
    def _generate_section_html(self):
        """Generate section pages (blog/posts.html, works/posts.html)"""
        with open(self.section_template, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Generate for each section
        for section in ['blog', 'works']:
            posts = self.registry.get_posts_by_type(section)
            
            # Generate posts HTML
            posts_html = ''
            for post in posts:
                post_url = f"{post['path']}/post.html"
                posts_html += f'<li><a href="{post_url}">{post["title"]}</a> ({post["date"]})</li>\n'
            
            # Replace template variables
            variables = {
                'posts': posts_html,
                'section': section.title()
            }
            section_html = self._replace_template_vars(template, variables)
            
            # Write section file
            section_dir = self.output_dir / section
            section_dir.mkdir(exist_ok=True)
            with open(section_dir / 'posts.html', 'w', encoding='utf-8') as f:
                f.write(section_html)

    def _update_registry(self, dir_name: str):
        """Update or insert post in registry"""
        post_data = {
            'id': dir_name,
            'type': self.post_type,
            'title': self.post_title,
            'date': self.post_date,
            'path': dir_name
        }
        
        try:
            # Try to update existing post
            self.registry.update_post(dir_name, post_data)
        except:
            # If update fails, insert new post
            self.registry.add_post(post_data)

    def generate(self):
        """Generate all required files"""
        try:
            # Read markdown content
            with open(self.post_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create post directory
            dir_name, post_dir = self._create_post_directory()
            
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
                'section': self.post_type.title()
            }
            
            post_html = self._replace_template_vars(template, post_vars)
            
            # Write post HTML with new filename
            with open(post_dir / 'post.html', 'w', encoding='utf-8') as f:
                f.write(post_html)
            
            # Update registry
            self._update_registry(dir_name)
            
            # Generate index and section pages
            self._generate_index_html()
            self._generate_section_html()
            
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