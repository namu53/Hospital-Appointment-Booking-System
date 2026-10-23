from app import create_app, db

app = create_app()

if __name__ == '__main__':
    # Run the application in debug mode for development
    app.run(debug=True)
