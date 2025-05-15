# JC's Website

My website. For free thanks to the generosity of Github. In return I offer you my data.


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
