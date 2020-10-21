import flask
import boto3

from . import query_validation
from data_layer import Redshift as SQL
from ..api import AlmacenAPI, api
from hashlib import sha1

query_blueprint = flask.Blueprint('query', __name__, url_prefix='/companies/<identifier>/query')

@query_blueprint.route('/run', methods=['POST'])
@api.check_privileges([AlmacenAPI.Privilege.reader])
def run(identifier):
  body = api.valid_body_from_request(
    request=flask.request, 
    schema=query_validation.post_run_schema
  )

  s3_options = api.s3_configuration
  s3_bucket = s3_options['bucket_name']
  query_text = body['query']
  query_hash = sha1(query_text.encode('utf-8')).hexdigest()
  path = s3_options['bucket_directory'] + f'/{identifier}-{query_hash}'
  results_url = f's3://{s3_bucket}/{path}'

  unload_query = _generate_unload_query(
    query_text=query_text,
    results_url=results_url,
    access_key_id=s3_options['access_key_id'],
    secret_access_key=s3_options['secret_access_key']
  )

  layer = SQL.Layer()
  layer.connect()
  unload_query.run(sql_layer=layer)
  layer.disconnect()

  region = s3_options['bucket_region']
  s3_key = f'{path}000.gz'
  unsigned_url = f'https://{s3_bucket}.s3.{region}.amazonaws.com/{s3_key}'

  s3 = boto3.resource(
    's3',
    aws_access_key_id=s3_options['access_key_id'],
    aws_secret_access_key=s3_options['secret_access_key']
  )
  s3_object = s3.Object(s3_bucket, s3_key)
  s3_object.copy_from(
    CopySource={'Bucket': s3_bucket, 'Key': s3_key}, 
    ContentType='text/csv', 
    ContentEncoding='gzip', 
    ContentDisposition=f'attachment; filename="{identifier}.csv"', 
    MetadataDirective='REPLACE'
  )

  if api.debug:
    s3_client = boto3.client(
      's3',
      aws_access_key_id=s3_options['access_key_id'],
      aws_secret_access_key=s3_options['secret_access_key']
    )
    signed_url = s3_client.generate_presigned_url(
      'get_object',
      Params={
        'Bucket': s3_bucket,
        'Key': s3_key
      },
      ExpiresIn=3600
    )

  return flask.jsonify({
    's3_bucket': s3_bucket,
    'results_path': f'{path}000.gz',
    'unsigned_url': unsigned_url,
    **({'signed_url': signed_url} if api.debug else {}),
  })

def _generate_unload_query(query_text: str, results_url: str, access_key_id: str, secret_access_key: str) -> SQL.Query:
  access_query = SQL.Query(
    query = f'access_key_id %s secret_access_key %s',
    substitution_parameters=(access_key_id, secret_access_key)
  )
  return SQL.Query(
      query = f'''
unload (%s)
to %s
{access_query.query}
parallel off
format as csv
allowoverwrite
gzip
header;
    ''',
      substitution_parameters=(
        query_text,
        results_url,
        *access_query.substitution_parameters
      )
    )