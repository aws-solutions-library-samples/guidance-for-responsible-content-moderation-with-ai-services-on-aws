
import sys
from os import listdir
from os.path import isfile, join
from concurrent.futures import ThreadPoolExecutor

import boto3
import re


def image_id(file_path):
    # file_path = 'C:/Users/test.txt'
    pattern = '[\w-]+?(?=\.)'

    # searching the pattern
    a = re.search(pattern, file_path)
    # printing the match
    name = a.group()
    print(name)
    return name


def index_collection(session, collection_id, image_file_name):
    print('---indexing faces:', image_file_name)
    client = session.client('rekognition')
    with open(image_file_name, "rb") as image:
        data = image.read()
        response = client.index_faces(CollectionId=collection_id,
                                      Image={'Bytes': data},
                                      MaxFaces=1,
                                      ExternalImageId=image_id(image_file_name),
                                      QualityFilter="AUTO",
                                      DetectionAttributes=['ALL'])
    print('---indexed faces:', image_file_name)


def init_collection(collection_id, faces_dir):
    create_collection(collection_id)
    # index face collection
    only_images = [f for f in listdir(faces_dir)
                   if isfile(join(faces_dir, f))
                   and (f.lower().endswith('png')
                        or f.lower().endswith('jpg')
                        or f.lower().endswith('jpeg'))]

    session = boto3.Session()
    print("\n---we have %d images" % len(only_images))

    with ThreadPoolExecutor(max_workers=5) as exe:
        tasks = []
        for image_name in only_images:
            print("---submitting %s images" % image_name)
            future = exe.submit(index_collection,
                                session=session,
                                collection_id=collection_id,
                                image_file_name='%s/%s' % (faces_dir, image_name))
            tasks.append(future)
        for task in tasks:
            task.done()


def create_collection(collection_id):
    client = boto3.client('rekognition')
    existing_collections = client.list_collections()

    if collection_id in existing_collections['CollectionIds']:
        return

    client.create_collection(CollectionId=collection_id)


def verify_collection(collection_id, image_file_name):
    with open(image_file_name, "rb") as image:
        image_bytes = image.read()
        response = boto3.Session().client('rekognition').search_faces_by_image(
            CollectionId=collection_id,
            FaceMatchThreshold=30,
            Image={
                'Bytes': image_bytes,
            },
            MaxFaces=1
        )

    print(f'-------response for face image{image_file_name}: {response}:')


if __name__ == '__main__':
    collection_name = 'moderation_custom_face_collection'
    create_collection(collection_name)

    args = sys.argv[1:]
    file_name = 'please_input_your_face.jpg'

    if len(args) >= 1:
        file_name = args[0]

    index_collection(boto3.Session(), collection_name, file_name)
