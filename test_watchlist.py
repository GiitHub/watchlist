import unittest

from watchlist import app, db
from watchlist.models import Movie, User
from watchlist.commands import forge, initdb

class WatchlistTestCase(unittest.TestCase):

    def setUp(self):

        # 更新配置
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
        )
        # 创建数据库和表
        db.create_all()

        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie', year='2022')
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()     # 创建测试客户端
        self.runner = app.test_cli_runner() # 创建测试命令运行器
    
    def tearDown(self):
        db.session.remove() # 清除数据库会话
        db.drop_all() # 删除数据库表

    # 测试程序实例是否存在
    def test_app_exist(self):
        self.assertIsNotNone(app)

    # 测试程序是否处于测试模式
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    # 测试404
    def test_404_page(self):
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)

    # 测试主页
    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data)
        self.assertIn('Test Movie', data)
        self.assertEqual(response.status_code, 200)

    # 测试辅助方法
    def login(self):
        self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)

    # 测试创建，更新和删除条目
    def test_create_item(self):
        self.login()

        response = self.client.post('/', data=dict(
            title="New Movie",
            year='2022'
        ), follow_redirects=True)

        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)


        response = self.client.post('/', data=dict(
            title="",
            year='2022'
        ), follow_redirects=True)

        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

        response = self.client.post('/', data=dict(
            title="New Movie",
            year=''
        ), follow_redirects=True)

        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)
    
    # 测试更新条目
    def test_update_item(self):
        self.login()

        # 获取数据
        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit Item', data)
        self.assertIn('Test Movie', data)
        self.assertIn('2022', data)

        # 正确输入
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited',
            year='2022'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('New Movie Edited', data)
        self.assertIn('Item updated.', data)

        # 电影名为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='',
            year='2022'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid input.', data)
        self.assertNotIn('Item updated.', data)

        # 年份为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited Again',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid input.', data)
        self.assertNotIn('Item updated.', data)
        self.assertNotIn('New Movie Edited Again', data)

    # 测试删除条目
    def test_delete_item(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item deleted.', data)
        self.assertNotIn('Test Movie', data)

    # 测试认证相关功能

    # 登陆保护
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('add', data)
        self.assertNotIn('<form method="post">', data)
        
    # 测试登录
    def test_login(self):
        # 登陆成功
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('add', data)
        self.assertIn('<form method="post">', data)

        # 使用错误密码登录
        response = self.client.post('/login', data=dict(
            username='test',
            password='123456'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 使用错误用户名登录
        response = self.client.post('/login', data=dict(
            username='tst',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 使用空用户名登录
        response = self.client.post('/login', data=dict(
            username='',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

        # 使用空密码
        response = self.client.post('/login', data=dict(
            username='test',
            password=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)


    # 测试登出
    def test_logout(self):
        self.login()
        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('add', data)
        self.assertNotIn('<form method="post">', data)


    # 测试设置
    def test_settings(self):
        self.login()
        
        # 设置页面
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Settings', data)
        self.assertIn('Your name', data)

        # 更新设置
        response = self.client.post('/settings', data=dict(
            name='test setting'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Settings updated.', data)
        self.assertIn('test setting', data)

        # 更新设置，name为空
        response = self.client.post('/settings', data=dict(
            name='',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Invalid input.', data)
        self.assertNotIn('Settings updated.', data)


    # 测试命令

    # 测试虚拟数据
    def test_forge_command(self):
        result = self.runner.invoke(forge)
        self.assertIn('Done.', result.output)
        self.assertNotEqual(Movie.query.count(), 0)

    # 测试初始化数据库
    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    # 测试生成管理员账户
    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'test_admin', '--password', '123'])
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'test_admin')   
        self.assertTrue(User.query.first().validate_password('123'))

    # 测试更新管理员账户
    def test_admin_command_update(self):
        result = self.runner.invoke(args=['admin', '--username', 'test_admin', '--password', '123'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'test_admin')   
        self.assertTrue(User.query.first().validate_password('123'))



if __name__ == '__main__':
    unittest.main()
    






