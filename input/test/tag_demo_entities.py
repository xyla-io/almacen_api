import json

parse_response = json.loads('''
{
    "message": "1 names parsed.",
    "name_tags": {
        "CAMPAIGNNAME1": {
            "tag1": "value1"
        }
    },
    "success": true
}
''')

entity_map = json.loads('''
{
  "Snapchat": [
    [
      "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    ],
    [
      "CAMPAIGNNAME1"
    ]
  ]
}
''')

tag_updates = []
for channel, mapping in entity_map.items():
  id_to_name_map = dict(zip(mapping[0], mapping[1]))
  tag_updates.extend([
    {
      'url': f'channel_entity://{channel}/campaign/{i}',
      'key': k,
      'value': v,
    }
    for i, n in id_to_name_map.items()
    for k, v in parse_response['name_tags'][n].items()
  ])

print(json.dumps({'tags': tag_updates}))