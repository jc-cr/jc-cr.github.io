import os
import shutil
import re
import logging
import subprocess
import traceback
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'some_secret_key'  # needed for flashing messages

# This should match the mounted directory in docker-compose.yaml
MARKDOWN_DIR = '/app/markdown_files'


def create_output_directory(file_path, post_type):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = os.path.join(f"/app/{post_type}", f"{base_name}_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Created output directory: {output_dir}")
    return output_dir


def copy_images(content, src_dir, dest_dir):
    # Pattern for Obsidian-style wiki links
    wiki_pattern = r'!\[\[(.*?)\]\]'

    # Find all image references
    wiki_images = re.findall(wiki_pattern, content)

    # Process Obsidian-style wiki links
    for image in wiki_images:
        # Walk thw source until the image is found
        src_path = os.path.join(MARKDOWN_DIR, image)
        logger.debug(f"Checking for image at: {src_path}")

        for root, dirs, files in os.walk(src_dir):
            if os.path.basename(image) in files:
                src_path = os.path.join(root, os.path.basename(image))
                break

        if os.path.exists(src_path):
            dest_path = os.path.join(dest_dir, os.path.basename(image))
            shutil.copy2(src_path, dest_path)
            # Update the image reference in the content
            content = content.replace(
                f'![[{image}]]', f'![{os.path.basename(image)}]({os.path.basename(image)})')
            logger.info(f"Copied image: {src_path} to {dest_path}")

        else:
            logger.warning(f"Image not found: {src_path}")

    return content


def create_html_template(css_path):
    try:
        template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title$ - JC's Website</title>
    <link href="/style/main.css" rel="stylesheet"/>
</head>
<body>
    <header>
        <h1><a href="/">JC's Website</a></h1>
        <p>
            <a href="/about.html">About</a> |
            <a href="/works/posts.html">Works</a> |
            <a href="/blog/posts.html">Blog</a>
        </p>
    </header>
    <main>
    $body$
    </main>
</body>
</html>
"""
        return template
    except Exception as e:
        logger.error(f"Error creating HTML template: {str(e)}")
        raise


def convert_markdown(file_path, output_dir):
    try:
        logger.info(f"Starting conversion of {file_path}")
        with open(file_path, 'r') as f:
            content = f.read()

        # The source directory is the mounted Markdown directory
        src_dir = MARKDOWN_DIR
        logger.info(f"Source directory: {src_dir}")

        content = copy_images(content, src_dir, output_dir)

        temp_md = os.path.join(output_dir, "temp.md")
        with open(temp_md, 'w') as f:
            f.write(content)
        logger.info(f"Wrote temporary Markdown file: {temp_md}")

        output_file = os.path.join(
            output_dir, f"{os.path.splitext(os.path.basename(file_path))[0]}.html")

        # Adjust this path to where your CSS file is located
        css_path = '/app/style/main.css'
        template = create_html_template(css_path)
        temp_template = os.path.join(output_dir, "temp_template.html")
        with open(temp_template, 'w') as f:
            f.write(template)
        logger.info(f"Wrote temporary template file: {temp_template}")

        logger.info("Running pandoc command...")
        result = subprocess.run(["pandoc", temp_md, "-o", output_file, "--standalone",
                                f"--template={temp_template}"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Pandoc error: {result.stderr}")
            raise Exception(f"Pandoc failed with error: {result.stderr}")

        os.remove(temp_md)
        os.remove(temp_template)

        logger.info(f"Conversion complete. Output file: {output_file}")

        return output_file
    except Exception as e:
        logger.error(f"Error in convert_markdown: {str(e)}")
        logger.error(traceback.format_exc())
        raise


ALLOWED_EXTENSIONS = {'md', 'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logger.info("POST request received")
        logger.debug(f"Request form: {request.form}")
        logger.debug(f"Request files: {request.files}")

        try:
            if 'markdown' not in request.files:
                logger.warning("No 'markdown' file in request")
                return "No file part", 400

            file = request.files['markdown']

            if file.filename == '':
                logger.warning("No selected file")
                return "No selected file", 400

            post_type = request.form.get('post_type')
            if not post_type:
                logger.warning("No post type specified")
                return "No post type specified", 400

            logger.info(f"Post type: {post_type}")

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(MARKDOWN_DIR, filename)
                file.save(file_path)
                logger.info(f"Saved Markdown file to: {file_path}")

                output_dir = create_output_directory(file_path, post_type)
                logger.info(f"Created output directory: {output_dir}")
                output_file = convert_markdown(file_path, output_dir)
                logger.info(f"Conversion complete. Output file: {output_file}")

                return f"Conversion complete. Output file: {output_file}", 200
            else:
                return "Invalid file type", 400
        except Exception as e:
            logger.error(f"Error in index route: {str(e)}")
            logger.error(traceback.format_exc())
            return f"An error occurred: {str(e)}", 500

    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
