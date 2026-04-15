import json
import base64
import uuid

# Load and parse group manager data
with open('/workspace/omni-group-manager-2026-04-15T07-05.json', 'r') as f:
    gm_data = json.load(f)

subgroup_order = json.loads(base64.b64decode(gm_data['values']['subgroup_order']['_data']).decode())
main_groups = json.loads(base64.b64decode(gm_data['values']['main_catalog_groups']['_data']).decode())
image_urls = json.loads(base64.b64decode(gm_data['values']['catalog_group_image_urls']['_data']).decode())

# Load and parse aio metadata
with open('/workspace/omni-aiometadata-full-catalogs-2026-04-15T07-10-29.json', 'r') as f:
    aio_data = json.load(f)

# Build catalog mapping from aio metadata
catalog_mapping = {}
for c in aio_data['catalogs']:
    name = c['name'].strip()
    if name.startswith('[Discover]'):
        cat = 'Discover'
        sub = name.replace('[Discover]', '').strip()
    elif name.startswith('[Streaming Services]'):
        cat = 'Streaming Services'
        sub = name.replace('[Streaming Services]', '').strip()
        sub = sub.replace('(Movies)', '').replace('(Shows)', '').replace('(Anime)', '').strip()
    elif name.startswith('[Genres]'):
        cat = 'Genres'
        sub = name.replace('[Genres]', '').strip()
        sub = sub.replace('(Movies)', '').replace('(Shows)', '').strip()
    elif name.startswith('[Collections]'):
        cat = 'Collections'
        sub = name.replace('[Collections]', '').strip()
        sub = sub.replace('(Movies)', '').replace('(Shows)', '').strip()
        # Also remove (All) suffix for collections
        sub = sub.replace('(All)', '').strip()
    elif name.startswith('[Directors]'):
        cat = 'Directors'
        sub = name.replace('[Directors]', '').strip()
        sub = sub.replace('(Movies)', '').replace('(Shows)', '').strip()
        # Also remove (All) suffix for directors
        sub = sub.replace('(All)', '').strip()
    elif name.startswith('[Actors]'):
        cat = 'Actors'
        sub = name.replace('[Actors]', '').strip()
        sub = sub.replace('(Movies)', '').replace('(Shows)', '').strip()
        # Also remove (All) suffix for actors
        sub = sub.replace('(All)', '').strip()
    elif name.startswith('[Decades]'):
        cat = 'Decades'
        sub = name.replace('[Decades]', '').strip()
        sub = sub.replace('(Movies)', '').replace('(Shows)', '').strip()
    else:
        continue
    
    key = (cat, sub)
    if key not in catalog_mapping:
        catalog_mapping[key] = []
    catalog_mapping[key].append({'catalogId': c['id'], 'type': c['type']})

# Fix Crunchyroll duplicate entry
if ('Streaming Services', 'Crunchyroll   2') in catalog_mapping:
    if ('Streaming Services', 'Crunchyroll') in catalog_mapping:
        catalog_mapping[('Streaming Services', 'Crunchyroll')].extend(catalog_mapping[('Streaming Services', 'Crunchyroll   2')])
    del catalog_mapping[('Streaming Services', 'Crunchyroll   2')]

# Fix Christmas duplicate entry  
if ('Genres', 'Christmas  2') in catalog_mapping:
    if ('Genres', 'Christmas') in catalog_mapping:
        # Merge unique entries
        existing_ids = set(item['catalogId'] for item in catalog_mapping[('Genres', 'Christmas')])
        for item in catalog_mapping[('Genres', 'Christmas  2')]:
            if item['catalogId'] not in existing_ids:
                catalog_mapping[('Genres', 'Christmas')].append(item)
    del catalog_mapping[('Genres', 'Christmas  2')]

# Generate output - hierarchical structure with folders array
output = []

# Map main group IDs to their info
for group_id, group_info in main_groups.items():
    category_name = group_info['name']
    poster_type = group_info['posterType'].upper()  # LANDSCAPE or POSTER
    subgroup_names = group_info['subgroupNames']
    
    # Get image URL for the main category
    cover_url = image_urls.get(category_name, "")
    
    # Create folders array for subgroups
    folders = []
    for subgroup_name in subgroup_names:
        # Get image URL for subgroup
        sub_cover_url = image_urls.get(subgroup_name, "")
        
        # Get catalog sources from mapping
        catalog_sources = []
        key = (category_name, subgroup_name)
        if key in catalog_mapping:
            for item in catalog_mapping[key]:
                catalog_sources.append({
                    "addonId": "aio-metadata",
                    "catalogId": item['catalogId'],
                    "type": item['type']
                })
        
        subfolder_obj = {
            "id": str(uuid.uuid4()),
            "title": subgroup_name,
            "_coverMode": "image",
            "coverImageUrl": sub_cover_url,
            "tileShape": poster_type,
            "catalogSources": catalog_sources
        }
        folders.append(subfolder_obj)
    
    # Create main category object with folders array
    main_category = {
        "id": str(uuid.uuid4()),
        "title": category_name,
        "_coverMode": "image",
        "coverImageUrl": cover_url,
        "tileShape": poster_type,
        "catalogSources": [],
        "folders": folders
    }
    output.append(main_category)

# Write output
with open('/workspace/media-library-layout.json', 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Generated {len(output)} objects")
print("Output written to /workspace/media-library-layout.json")
