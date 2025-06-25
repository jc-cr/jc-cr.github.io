# JC's Website
My website. For free thanks to the generosity of Github. In return I offer you my data.

## Post Generation
Posts are generated using a combination of Markdown files and a custom static site generator that converts them to HTML.

### Creating New Posts
1. Run the post GUI with Docker Compose:

```bash
docker compose up post_gui --remove-orphans --abort-on-container-exit
   ```
2. Select a Markdown file, enter title and date, and select appropriate tags
3. Click "Create Post" to generate the HTML and update the indices

Each post is stored in `/webpage/posts/YYYYMMDD_title` with:
- `post.html` - The generated HTML content
- `meta.json` - Metadata including title, date, tags, and snippet
- Any media files (images, videos) referenced in the post

### Manually Updating Indices
If you need to regenerate all index files without creating a new post:

```bash
docker compose run --rm update_index
```

This will scan all posts and generate index files for all tags and an index of all posts.

## Adding an App 
A repository with just vanilla HTML, CSS, and JavaScript can be added to the apps dir as a submodule. 
Just make sure the workflow includes submodules like:
```yaml
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: true
```

## Environment Setup
Create a `.env` file in the `.docker` directory with:
```
OBSIDIAN_PATH=/path/to/your/obsidian/vault
```

This tells the container where to find your Markdown files.

## Viewing the Site Locally
The site can be viewed locally by running:
```bash
docker compose up view_page --remove-orphans --abort-on-container-exit
```

Then navigate to `http://localhost:8080`.

## GitHub Pages Deployment
The site uses a GitHub workflow to deploy to GitHub Pages. The workflow is triggered on push to the `main` branch.

During the build process:
1. Python dependencies are installed
2. The index generator runs to create index files for all tags
3. The site is deployed to GitHub Pages

The deployment process uses the static HTML files with no server-side processing, making it fast and secure.