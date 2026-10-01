import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
def get_logger(name:str,level:str="INFO",logfile:str|None=None)->logging.Logger:
    logger=logging.getLogger(name)
    numeric=getattr(logging,level.upper(),logging.INFO)
    logger.setLevel(numeric)
    has_stream=any(isinstance(h,logging.StreamHandler) and not isinstance(h,RotatingFileHandler) for h in logger.handlers)
    has_file=any(isinstance(h,RotatingFileHandler) for h in logger.handlers)
    formatter=logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s",datefmt="%Y-%m-%d %H:%M:%S")
    if not has_stream:
        handler=logging.StreamHandler()
        handler.setLevel(numeric)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if not has_file:
        logfile=logfile or "logs/app.log"
        Path(logfile).parent.mkdir(parents=True,exist_ok=True)
        handler=RotatingFileHandler(logfile,maxBytes=1_000_000,backupCount=5,encoding="utf-8")
        handler.setLevel(numeric)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.propagate=False
    return logger
class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self,msg:Any,kwargs:dict[str,Any])->tuple[Any,dict[str,Any]]:
        extra=self.extra.copy() if self.extra else {}
        for key in [k for k in kwargs if k not in ("exc_info","stack_info","stacklevel","extra")]:
            extra[key]=kwargs.pop(key)
        if extra:msg=f"{msg} {' '.join(f'{k}={v}' for k,v in extra.items())}"
        return msg,kwargs
def get_context_logger(name:str,base_extra:dict|None=None,level:str="INFO",logfile:str|None=None,**kwargs)->ContextLoggerAdapter:
    extra=base_extra.copy() if base_extra else {}
    extra.update(kwargs)
    return ContextLoggerAdapter(get_logger(name,level,logfile),extra)