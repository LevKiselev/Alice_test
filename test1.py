import logging

# logging.basicConfig(filename='test1.log')
logging.basicConfig(filename='test1.log', format='%(asctime)s %(levelname)s %(name)s %(message)s')

def log():
    for i in range(10):
        logging.warning(i)


if __name__ == '__main__':
    log()