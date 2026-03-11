import pytest
from app import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    # Matikan CSRF jika Anda menggunakan Flask-WTF agar testing lebih mudah
    app.config['WTF_CSRF_ENABLED'] = False 
    with app.test_client() as client:
        yield client

# 1. TEST HALAMAN INDEX
def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Selamat datang" in response.data

# 2. TEST REGISTRASI: BERHASIL
@patch('app.get_db_connection')
def test_register_success(mock_db, client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_db.return_value = mock_conn
    mock_cur.fetchone.return_value = None 
    
    response = client.post('/register', data={
        'username': 'userbaru123',
        'password': 'Password123'
    }, follow_redirects=True)
    
    assert b"Registrasi berhasil" in response.data

# 3. TEST LOGIN: BERHASIL
@patch('app.get_db_connection')
# Ganti target patch ke werkzeug secara langsung karena 'app' tidak mengekspornya
@patch('werkzeug.security.check_password_hash') 
def test_login_success(mock_check, mock_db, client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_db.return_value = mock_conn
    
    # Mock data user dari database
    mock_cur.fetchone.return_value = (1, 'testuser', 'hashed_password_dummy')
    
    # Paksa hasil pengecekan password menjadi True
    mock_check.return_value = True
    
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Halo, testuser" in response.data

# 4. TEST LOGIN: PASSWORD SALAH
@patch('app.get_db_connection')
@patch('werkzeug.security.check_password_hash')
def test_login_wrong_password(mock_check, mock_db, client):
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value.fetchone.return_value = (1, 'testuser', 'hashed_dummy')
    
    # Simulasi password salah
    mock_check.return_value = False 
    
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'salah'
    }, follow_redirects=True)
    
    assert b"Password salah" in response.data

# 5. TEST LOGOUT
def test_logout(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'testuser'
    
    response = client.get('/logout', follow_redirects=True)
    # Setelah logout harusnya kembali ke halaman login atau home
    assert b"Login" in response.data or b"Selamat datang" in response.data