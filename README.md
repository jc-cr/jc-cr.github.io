# JC's Website

This is the source code for my personal website which uses a static site generator to convert Markdown files from Obsidian into HTML.

## Directory Structure

```
.
├── data/               # Contains SQLite database
├── scripts/           # Python scripts
├── templates/         # HTML templates
├── webpage/          # Website content
│   ├── about/       # About page
│   ├── blog/        # Blog posts
│   ├── style/       # CSS files
│   └── works/       # Works/projects
└── docker/          # Docker configuration
```

## Creating New Posts

1. Create a new Markdown file in your Obsidian vault
2. Set up environment variables in `.env`:
   ```
   POST_TYPE="blog"          # or "works"
   POST_TITLE="Your Title"
   POST_DATE="YYYY-MM-DD"    # Optional, defaults to today
   OBSIDIAN_PATH="/path/to/obsidian/vault"
   POST_PATH="/path/to/markdown/file.md"
   ```
3. Run the post generation service:
   ```bash
cd .docker
docker compose run --rm new_post
   ```

## Adding an App 

A repository with just vanilla HTML, CSS, and JavaScript can be added to the apps dir as a submodule. 
Just make sure the workflow includes submodules like:
```yaml

      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: true
```

### Viewing the Site Locally

The site can be viewed locally by running `docker compose up view_page` and navigating to `http://localhost:8080`.

## GitHub Pages Deployment

The site uses a GitHub workflow to deploy the site to GitHub Pages. The workflow is triggered on push to the `main` branch and builds the site using the static site generator.
During this process the sync_db service is run to update the SQLite database with the latest posts and remove any deleted posts.
