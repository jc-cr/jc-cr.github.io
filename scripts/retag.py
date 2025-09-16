#!/usr/bin/env python3
import os
import json
from pathlib import Path

def consolidate_tags(base_dir=None):
    """
    Consolidate 'blog' and 'haikuesque' tags into 'pennings'
    
    Args:
        base_dir: Base directory of the website (default: current directory)
    """
    base_dir = Path(base_dir if base_dir else '.')
    posts_dir = base_dir / 'webpage' / 'posts'
    
    if not posts_dir.exists():
        print(f"Posts directory not found: {posts_dir}")
        return
    
    updated_count = 0
    
    # Process all post directories
    for post_dir in posts_dir.glob('*/'):
        meta_file = post_dir / 'meta.json'
        
        if not meta_file.exists():
            continue
            
        try:
            # Read the meta.json file
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta_data = json.load(f)
            
            # Check if tags need updating
            tags = meta_data.get('tags', [])
            original_tags = tags.copy()
            
            # Replace 'blog' and 'haikuesque' with 'penning'
            updated_tags = []
            has_blog_or_haiku = False
            
            for tag in tags:
                if tag.lower() in ['blog', 'haikuesque', 'pennings']:
                    has_blog_or_haiku = True
                    if 'penning' not in updated_tags:
                        updated_tags.append('penning')
                else:
                    updated_tags.append(tag)
            
            # Only update if there were changes
            if has_blog_or_haiku:
                meta_data['tags'] = updated_tags
                
                # Write back to file
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, indent=2)
                
                updated_count += 1
                print(f"Updated {post_dir.name}: {original_tags} → {updated_tags}")
                
        except Exception as e:
            print(f"Error processing {meta_file}: {e}")
    
    print(f"\nConsolidation complete. Updated {updated_count} posts.")
    return updated_count

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Consolidate blog and haikuesque tags into pennings")
    parser.add_argument('--base-dir', help="Base directory of the website (default: current directory)")
    parser.add_argument('--dry-run', '-n', action='store_true', help="Show what would be changed without making changes")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        # You could add dry run logic here
    
    consolidate_tags(args.base_dir)