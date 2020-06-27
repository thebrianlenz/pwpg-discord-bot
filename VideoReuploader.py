import asyncio
from configparser import ConfigParser
from functools import partial

import aiohttp
import boto3
import botocore
import discord
import praw
import requests
import youtube_dl
from botocore.exceptions import ClientError
from discord.ext import commands
from discord.ext.commands import Bot


class VideoReuploader(commands.Cog):
	def __init__(self, bot: Bot):
		self.bot = bot
		config = ConfigParser()
		config.read('config.ini')

		CLIENT_ID = config.get('praw', 'reddit_client_id')
		CLIENT_SECRET = config.get('praw', 'reddit_client_secret')
		USER_AGENT = "python:pwpg.bot:v0.0.1 (by u/pwpg_bot)"

		AWS_ACCESS_KEY_ID = config.get('aws', 'access_key_id')
		AWS_SECRET_ACCESS_KEY = config.get('aws', 'secret_access_key')
		self.AWS_BUCKET = config.get('aws', 'bucket_name')
	
		self.reddit = praw.Reddit(client_id = CLIENT_ID,
					 client_secret = CLIENT_SECRET,
					 user_agent = USER_AGENT)

		self.aws_client = boto3.client('s3',
							aws_access_key_id = AWS_ACCESS_KEY_ID,
							aws_secret_access_key = AWS_SECRET_ACCESS_KEY)

	@commands.command(name='check',
						description = 'Check aws for object name',
						pass_context = True)
	async def check_aws(self, context, target_url):
		"""Takes a target URL of a v.reddit video, rehosts it, and returns a public URL.

		Args:
			context (context): Context of the invoking command
			target_url (str): URL of a v.reddit video
		"""
		try:
			msg = await context.send("... rehosting v.reddit ...")
			result = await self.grab_vreddit(target_url)
			print(result)
			await context.send(f'Rehosted: {result}')
			await msg.delete()
		except Exception as e:
			print(e)

	async def grab_vreddit(self, target_url):
		"""Takes a target URL of a v.reddit video and reuploads it to an S3 Bucket for rehosting.

		Using the title of the submission, the file is named and saved to the local disk, then uploaded 
		to S3. When the video exists on the Bucket, the public URL is returned.

		Args:
			target_url (str): A v.reddit URL

		Returns:
			str: The URL of the rehosted video
		"""
		submission = await self.get_submission_object(target_url)
		title_pattern = f'{submission.name}' # Removed {submission.title} to reduce name length
		heirarchy = f'videos/'
		ydl_opts = {'prefer_ffmpeg' : True,
			'outtmpl' : f'{heirarchy}{title_pattern}.%(ext)s'}

		ydl = youtube_dl.YoutubeDL(ydl_opts)

		info_dict = ydl.extract_info(submission.url, False)
		filename = f'{ydl.prepare_filename(info_dict)}'
		aws_file_path = f'{heirarchy}{title_pattern}.{info_dict["ext"]}'

		url = self.aws_locate_url(aws_file_path)

		if url is None:
			# needs to be uploaded
			print('No file found on AWS, downloading now')
			
			# ydl.download([submission.url]) ran in executor to prevent blocking
			to_run = partial(ydl.download, [submission.url])
			await self.bot.loop.run_in_executor(None, to_run)

			print('Uploading to AWS')
			
			#self.aws_upload(filename, aws_file_path) ran in executor to prevent blocking
			to_run = partial(self.aws_upload, filename, aws_file_path)
			await self.bot.loop.run_in_executor(None, to_run)

			url = self.aws_locate_url(aws_file_path)

		return url
		

	def aws_upload(self, local_file_path, aws_target_path):
		"""Uploads a file to S3 using the Bucket defined in config.ini
		
		The file uploaded is given the ContentType of video/mp4, and is made publicly readable.

		Args:
			local_file_path (str): The path of the local file
			aws_target_path (str): The location to upload within the S3 Bucket
		"""
		try:
			self.aws_client.upload_file(local_file_path, self.AWS_BUCKET, aws_target_path,
										ExtraArgs={'ContentType' : 'video/mp4',
													'ACL': 'public-read'})
		except Exception as e:
			print('Upload failed')
			print(e)

	def aws_locate_url(self, file_path):
		"""Takes an AWS file path and creates a public URL.

		Args:
			file_path (str): The file path for an object on AWS S3

		Returns:
			str: A public URL for an AWS S3 object or None if the object is not found
		"""
		try:
			self.aws_client.head_object(Bucket = self.AWS_BUCKET, Key = file_path)
			url = self.aws_client.generate_presigned_url('get_object',
												Params = {'Bucket' : self.AWS_BUCKET,
															'Key' : file_path},
												ExpiresIn = 86400)
			
			return self.clean_aws_url(url)
		except ClientError as e:
			print(e)
			return None

	async def get_submission_object(self, target_url):
		"""Takes a target_url and passes it through requests to make sure that we aren't being redirected.

		Args:
			target_url (str): A URL

		Returns:
			Reddit.submission: A Reddit submission object
		"""
		async with aiohttp.request(method = 'HEAD', url = target_url, allow_redirects = True) as response:
			return self.reddit.submission(url = str(response.url))

	def clean_aws_url(self, aws_file_path):
		"""Cleans out the presigned signature for AWS.

		Args:
			aws_file_path (str): A full file path that has been generated for an AWS S3 object

		Returns:
			str: A "cleaned" version of a public AWS S3 object
		"""
		result = aws_file_path.partition("?AWSAccessKeyId=") # Removes the signature component of the URL
		return result[0]

def setup(bot):
	bot.add_cog(VideoReuploader(bot))

def teardown(bot):
	bot.remove_cog('VideoReuploader')
