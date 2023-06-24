class BaseConfig(object):
    #MONGO_URI = os.environ.get('MONGO_URI')
    #MONGO_URI = 'mongodb://localhost:27017/your-database'
    MONGODB_SETTINGS = {
        'host': 'mongodb://root:password@db:27017/admonish-grumbler-db?authSource=admin'
}
