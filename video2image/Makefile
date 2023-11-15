BASE_NAME=ffmpeg
DEPLOYMENT_BUCKET_NAME := $(ffmpeg-packaging-$$RANDOM)
DEPLOYMENT_KEY := $(shell echo $(BASE_NAME)-$$RANDOM.zip)
STACK_NAME := $(BASE_NAME)-lambda-layer

clean: 
	rm -rf build

build/bin/ffmpeg: 
	mkdir -p build/bin
	rm -rf build/ffmpeg*
	cd build; \
		curl https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar x
	mv build/ffmpeg*/ffmpeg build/ffmpeg*/ffprobe build/bin

build/layer.zip: build/bin/ffmpeg
	cd build && zip -r layer.zip bin

build/output.yml: build/layer.zip ffmpeg-lambda-layer/template.yml
	aws s3 cp build/layer.zip s3://$(DEPLOYMENT_BUCKET_NAME)/$(DEPLOYMENT_KEY)
	sed "s:DEPLOYMENT_BUCKET_NAME:$(DEPLOYMENT_BUCKET_NAME):;s:DEPLOYMENT_KEY:$(DEPLOYMENT_KEY):" ffmpeg-lambda-layer/template.yml > build/output.yml

build/lambda: lambda/lambda_function.py
	cp lambda/lambda_function.py build
	zip build/lambda.zip build/lambda_function.py

deploy: build/output.yml
	aws cloudformation deploy --template-file build/output.yml --stack-name $(STACK_NAME)
	aws cloudformation describe-stacks --stack-name $(STACK_NAME) --query Stacks[].Outputs[].OutputValue --output text)
	

