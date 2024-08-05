import os
import shutil
from pathlib import Path
import markdown
import yaml
import re

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

def read_index():
    with open('markdown/index.md', 'r') as f:
        return f.read().replace('$WEBSITE', WEBSITE_URL)

def convert_md_to_html(md_content, html_path):
    front_matter, content = read_yaml_front_matter(md_content)
    header_content = read_index()
    
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
        <title>{front_matter.get('title', 'Untitled')} | JC's Website</title>
        <link rel="stylesheet" href="/style/main.css">
    </head>
    <body>
        <header>
            {title}
            <p>{nav}</p>
        </header>
        <main>
            {main_html}
        </main>
    </body>
    </html>
    """

    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    with open(html_path, 'w') as f:
        f.write(html)

def process_directory(src_dir, dest_dir):
    posts = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.md'):
                md_path = os.path.join(root, file)
                rel_path = os.path.relpath(md_path, src_dir)
                
                # Special handling for about page
                if 'about' in rel_path:
                    html_path = os.path.join(dest_dir, 'about', 'index.html')
                else:
                    post_dir = os.path.dirname(rel_path)
                    html_path = os.path.join(dest_dir, post_dir, 'index.html')
                
                with open(md_path, 'r') as f:
                    md_content = f.read()
                convert_md_to_html(md_content, html_path)
                
                # Add post info to posts list (exclude about page)
                if 'about' not in rel_path:
                    front_matter, content = read_yaml_front_matter(md_content)
                    title = front_matter.get('title', os.path.basename(os.path.dirname(rel_path)))
                    snippet = get_snippet(content)
                    image = get_image(content, os.path.dirname(md_path))
                    posts.append({
                        'title': title,
                        'snippet': snippet,
                        'image': image,
                        'url': f"/{os.path.relpath(html_path, 'auto_gen')}"
                    })
            elif file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                # Copy image files to the destination
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, src_dir)
                dest_path = os.path.join(dest_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy2(src_path, dest_path)
    
    return posts

def create_index_redirect():
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url={WEBSITE_URL}/auto_gen/about/index.html">
        <title>Redirecting...</title>
    </head>
    <body>
        <p>If you are not redirected automatically, follow this <a href="{WEBSITE_URL}/auto_gen/about/index.html">link to the About page</a>.</p>
    </body>
    </html>
    """
    with open('index.html', 'w') as f:
        f.write(index_html)

def get_snippet(content):
    # Remove the title and image
    content = re.sub(r'^#.*\n\[\[.*\]\]\n', '', content, flags=re.MULTILINE)
    # Get the first 150 characters
    return content[:150] + '...' if len(content) > 150 else content

def get_image(content, post_dir):
    match = re.search(r'\[\[(.*)\]\]', content)
    if match:
        image_name = match.group(1)
        image_path = os.path.join(post_dir, image_name)
        if os.path.exists(image_path):
            return os.path.join(os.path.basename(post_dir), image_name)
    return None

def create_posts_html(posts, category, dest_dir):
    tiles = ''
    for post in posts:
        image_html = f'<img src="{post["image"]}" alt="Post image">' if post['image'] else ''
        tiles += f"""
        <div class="tile">
            <h2><a href="{post['url']}">{post['title']}</a></h2>
            {image_html}
            <p>{post['snippet']}</p>
        </div>
        """
    
    content = f"""
    <h1>{category.capitalize()} Posts</h1>
    {'<div class="tile-container">' + tiles + '</div>' if tiles else '<p>Nothing here yet...</p>'}
    """
    
    convert_md_to_html(content, os.path.join(dest_dir, category, 'posts.html'))

def create_index_redirect():
    index_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0; url={WEBSITE_URL}/auto_gen/about/about.html">
        <title>Redirecting...</title>
    </head>
    <body>
        <p>If you are not redirected automatically, follow this <a href="{WEBSITE_URL}/auto_gen/about/about.html">link to the About page</a>.</p>
    </body>
    </html>
    """
    with open('index.html', 'w') as f:
        f.write(index_html)

if __name__ == "__main__":
    # Generate all pages in auto_gen
    blog_posts = process_directory('markdown/blog', 'auto_gen/blog')
    works_posts = process_directory('markdown/works', 'auto_gen/works')
    process_directory('markdown', 'auto_gen')
    
    # Create posts.html for blog and works
    create_posts_html(blog_posts, 'blog', 'auto_gen')
    create_posts_html(works_posts, 'works', 'auto_gen')
    
    # Create index.html in the root directory as a redirect
    create_index_redirect()
    print("Site generated in 'auto_gen' directory, index.html created as redirect in root.")
