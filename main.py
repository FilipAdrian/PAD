from resources.user import User, Users
from config import api, app, check_db_connection, connect_to_gateway, env_args


# Add API resources
api.add_resource(Users, "/users", endpoint="users")
api.add_resource(User, "/users/<int:user_id>", endpoint="user-by-id")

if __name__ == "__main__":
    check_db_connection()
    connect_to_gateway()
    app.run(host=env_args["API_HOST"], port=env_args["API_PORT"], debug=True,
            threaded=True)  # Set up sever host,port enabled debug mode
