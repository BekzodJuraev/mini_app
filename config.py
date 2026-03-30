import environ


env = environ.Env()
environ.Env.read_env()
KEY=env('KEY')
MODEL=env('MODEL')

EMAIL_HOST=env('EMAIL_HOST')
EMAIL_PORT=env('EMAIL_PORT')
EMAIL_USE_TLS=env('EMAIL_USE_TLS')
EMAIL_HOST_USER=env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=env('EMAIL_HOST_PASSWORD')
DEBUG = env.bool('DEBUG', default=False)