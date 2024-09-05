# JC's Website

## How it works

I usally make notes in the Obsidian app which uses the markdown language. To not have to rewrite stuff and
reorganize content, I just convert those files to posts.

For development I use 2 docker container, one runs the website so I can see the changes as I work. The other container
hosts a service that converts markdown to html as well as copying associated images to a directory in either
`/blogs` or `/works`.

When I push to github the `update_posts.py` script runs and updates the `Latest:` posts and creates new posts
blocks in the respective posts.html.


