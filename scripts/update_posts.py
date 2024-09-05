import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

def get_project_root():
    return '/app/site' if os.path.exists('/app/site') else '.'

def get_directories(path):
    try:
        dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        print(f"Directories in {path}: {dirs}")
        return dirs
    except Exception as e:
        print(f"Error getting directories in {path}: {str(e)}")
        return []

def parse_directory_name(directory):
    match = re.match(r'(.+)_(\d{14})$', directory)
    if match:
        name = match.group(1).replace('_', ' ')
        timestamp = datetime.strptime(match.group(2), '%Y%m%d%H%M%S')
        return name, timestamp
    print(f"Failed to parse directory name: {directory}")
    return None, None

def update_posts_html(directory_path, posts_file, post_type):
    directories = get_directories(directory_path)
    posts = []

    for directory in directories:
        name, timestamp = parse_directory_name(directory)
        if name and timestamp:
            posts.append((name, timestamp, directory))

    posts.sort(key=lambda x: x[1], reverse=True)

    print(f"Posts for {directory_path}: {posts}")

    try:
        with open(posts_file, 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except Exception as e:
        print(f"Error reading {posts_file}: {str(e)}")
        return

    main = soup.find('main')
    if main:
        main.clear()
        h2 = soup.new_tag('h2')
        h2.string = f"{post_type}:"
        main.append(h2)
        ul = soup.new_tag('ul')
        for name, timestamp, directory in posts:
            li = soup.new_tag('li')
            a = soup.new_tag('a', href=f"{directory}/{name.replace(' ', '_')}.html")
            a.string = name
            li.append(a)
            li.append(f" - {timestamp.strftime('%B %d, %Y')}")
            ul.append(li)
        main.append(ul)
    else:
        print(f"Couldn't find main section in {posts_file}")
        return

    try:
        with open(posts_file, 'w') as f:
            f.write(str(soup))
        print(f"Updated {posts_file}")
    except Exception as e:
        print(f"Error writing to {posts_file}: {str(e)}")

def update_index_html(blog_posts, works_posts):
    print(f"Updating index.html with blog posts: {blog_posts}")
    print(f"Updating index.html with works posts: {works_posts}")

    project_root = get_project_root()
    index_file = os.path.join(project_root, 'index.html')

    try:
        with open(index_file, 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except Exception as e:
        print(f"Error reading {index_file}: {str(e)}")
        return

    main = soup.find('main')
    if main:
        main.clear()
        h2 = soup.new_tag('h2')
        h2.string = "Latest:"
        main.append(h2)
        ul = soup.new_tag('ul')
        all_posts = sorted(blog_posts + works_posts, key=lambda x: x[1], reverse=True)[:5]
        for name, timestamp, directory, post_type in all_posts:
            li = soup.new_tag('li')
            a = soup.new_tag('a', href=f"{post_type}/{directory}/{name.replace(' ', '_')}.html")
            a.string = name
            li.append(a)
            li.append(f" - {timestamp.strftime('%B %d, %Y')} ({post_type.capitalize()})")
            ul.append(li)
        main.append(ul)
    else:
        print(f"Couldn't find main section in {index_file}")
        return

    try:
        with open(index_file, 'w') as f:
            f.write(str(soup))
        print(f"Updated {index_file}")
    except Exception as e:
        print(f"Error writing to {index_file}: {str(e)}")

def main():
    project_root = get_project_root()
    blog_path = os.path.join(project_root, 'blog')
    works_path = os.path.join(project_root, 'works')
    blog_posts_file = os.path.join(blog_path, 'posts.html')
    works_posts_file = os.path.join(works_path, 'posts.html')

    update_posts_html(blog_path, blog_posts_file, "Blog")
    update_posts_html(works_path, works_posts_file, "Works")

    blog_posts = []
    works_posts = []

    for directory in get_directories(blog_path):
        name, timestamp = parse_directory_name(directory)
        if name and timestamp:
            blog_posts.append((name, timestamp, directory, 'blog'))

    for directory in get_directories(works_path):
        name, timestamp = parse_directory_name(directory)
        if name and timestamp:
            works_posts.append((name, timestamp, directory, 'works'))

    print(f"Final blog posts: {blog_posts}")
    print(f"Final works posts: {works_posts}")

    update_index_html(blog_posts, works_posts)

if __name__ == "__main__":
    main()