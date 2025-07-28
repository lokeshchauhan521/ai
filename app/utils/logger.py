# to get error or info logs
import logging as logger

class FileLogs:
    def get_logger(self, name="AI_analysis"):

        formatter = logger.Formatter("[%(asctime)s]:[%(name)s]:[%(funcName)s:%(lineno)s]:[%(levelname)s]:%(message)s")
        rootLogger = logger.getLogger(name)
        if not rootLogger.handlers:
            fileHandler = logger.FileHandler("logs/app.log")
            fileHandler.setFormatter(formatter)
            rootLogger.addHandler(fileHandler)
            rootLogger.setLevel(logger.INFO)
            rootLogger.propagate = False
        
        return rootLogger