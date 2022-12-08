from flask import render_template
from watchlist import app

@app.errorhandler(404) # 传入错误代码
def page_not_found(e): # 接受异常对象作为参数
    return render_template('errors/404.html'), 404

