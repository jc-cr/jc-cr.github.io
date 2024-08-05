import os
import shutil
from pathlib import Path
import markdown
import yaml

def read_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

config = read_config()
WEBSITE_URL = config['website_url']

def read_yaml_front_matter(md_content):
    lines = md_content.split('\n')
    if lines[0] == '---':
        end = lines[1:].index('---') + 1
        front_matter = yaml.safe_load('\n'.join(lines[1:end]))
        content = '\n'.join(lines[end+1:])
        return front_matter, content
    return {}, md_content

def read_header():
    with open('markdown/header_top.md', 'r') as f:
        return f.read().replace('$WEBSITE', WEBSITE_URL)

def convert_md_to_html(md_path, html_path, is_index=False):
    with open(md_path, 'r') as f:
        md_content = f.read()
    
    front_matter, content = read_yaml_front_matter(md_content)
    header_content = read_header()
    
    # Convert header and main content to HTML
    header_html = markdown.markdown(header_content)
    main_html = markdown.markdown(content)

    # Extract title and navigation from header_html
    header_lines = header_html.split('\n')
    title = header_lines[0]
    nav = header_lines[1] if len(header_lines) > 1 else ''

    # Simple HTML template
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{"Home" if is_index else front_matter.get('title', 'Untitled')} | JC's Website</title>
        <link rel="stylesheet" href="/style/main.css">
    </head>
    <body>
        <header>
            {title}
            <p>{nav}</p>
        </header>
        <main>
            {main_html if not is_index else ''}
        </main>
    </body>
    </html>
    """

    # Only create directories if html_path is not in the root
    if os.path.dirname(html_path):
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
    
    with open(html_path, 'w') as f:
        f.write(html)

def process_directory(src_dir, dest_dir):
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                rel_path = os.path.relpath(md_path, src_dir)
                html_path = os.path.join(dest_dir, rel_path.replace('.md', '.html'))
                
                # For blog posts, ensure they're in the correct directory structure
                if 'blog' in rel_path:
                    parts = rel_path.split(os.sep)
                    if len(parts) > 2:
                        date_parts = parts[1].split('-')[:3]
                        html_path = os.path.join(dest_dir, 'blog', *date_parts, parts[1], 'index.html')
                
                convert_md_to_html(md_path, html_path)
            else:
                # Copy non-markdown files (e.g., images) to the destination
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, src_dir)
                dest_path = os.path.join(dest_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)

def create_index():
    convert_md_to_html('markdown/header_top.md', 'index.html', is_index=True)

if __name__ == "__main__":
    process_directory('markdown', '.')
    create_index()
    print("Site generated in the current directory.")
