import boto3
import os

S3_BUCKET = "ContentModerationDemo"
FFMPEG = 'ffmpeg'
FFMPEG_ARG = '-vf fps=1'

def get_environment_variables():
    global S3_BUCKET
    if os.environ.get('S3_BUCKET') is not None:
        S3_BUCKET = os.environ['S3_BUCKET']
        print('environment variable S3_BUCKET was found: {}'.format(S3_BUCKET))

def get_video_from_s3():
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    bucket = s3.Bucket(S3_BUCKET)
    for obj in bucket.objects.all():
        if obj.key.endswith('.mp4'):
            print('found mp4 file: {}'.format(obj.key))
            s3_client.download_file(S3_BUCKET, obj.key, '/tmp/video.mp4')
            return obj.key
    print('video downloaded')
    
def extract_frames():
    print('extracting frames')
    if not os.path.exists('/tmp/frames'):
        os.makedirs('/tmp/frames')
    cmd = '{} -hide_banner -nostats -loglevel error -y -i /tmp/video.mp4 {} /tmp/frames/%04d.jpg'.format(FFMPEG, FFMPEG_ARG)
    os.system(cmd)
    print('frames extracted')

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(S3_BUCKET)
    frame_count = len([name for name in os.listdir('/tmp/frames') if os.path.isfile(os.path.join('/tmp/frames', name))])
    print('frame count: {}'.format(frame_count))
    for i in range(1, frame_count):
        i = '{:04d}'.format(i)
        key = 'frames/{}.jpg'.format(i)
        bucket.upload_file('/tmp/frames/{}.jpg'.format(i), key)
        print('uploaded frame: {}'.format(key))
        
    print('key frames uploaded to s3')

def lambda_handler(event, context):
    if 'source' in event:
        if event['source'] == 'aws.events':
            return 'warm up invocation'

    get_environment_variables();
    get_video_from_s3();
    extract_frames();

    return 'success!'
        
if __name__ == '__main__':
    # for local testing
    FFMPEG = 'ffmpeg' # use local mac version 
    os.environ['S3_BUCKET'] = 'content-moderation-demo-128568931530'
    this_event = {'source': 'test'}
            
    boto3.setup_default_session(profile_name='oregon')

    print(lambda_handler(this_event, None))
    
    with open('logs', 'w') as outfile:
        outfile.write('awslogs get /aws/lambda/catfinder5004-parse ALL --watch')
