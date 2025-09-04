from app import create_app

if __name__ == '__main__':
    app = create_app()
    print("🏥 Hospital Booking System Starting...")
    print("📍 Access the application at: http://localhost:4000")
    print("👤 Admin Login: admin@hospital.com / admin123")
    print("👨‍⚕️ Patient Login: patient@hospital.com / patient123")
    app.run(debug=True, host='0.0.0.0', port=4000)
