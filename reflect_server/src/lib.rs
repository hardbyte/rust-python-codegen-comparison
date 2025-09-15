use std::sync::{Arc, Mutex};

pub fn builder() -> reflectapi::Builder<Arc<AppState>> {
    reflectapi::Builder::new()
        .name("Reflect API Demo")
        .description("A simple API using reflectapi for Rust-Python interop demo")
        .route(get_message, |b| {
            b.name("message.get")
                .readonly(true)
                .description("Get a simple message")
        })
        .route(create_user, |b| {
            b.name("user.create")
                .description("Create a new user")
        })
        .route(get_users, |b| {
            b.name("users.list")
                .readonly(true)
                .description("List all users")
        })
}

#[derive(Debug)]
pub struct AppState {
    users: Mutex<Vec<model::User>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            users: Mutex::new(vec![
                model::User {
                    id: 1,
                    username: "alice".to_string(),
                    email: "alice@example.com".to_string(),
                    active: true,
                },
                model::User {
                    id: 2,
                    username: "bob".to_string(),
                    email: "bob@example.com".to_string(),
                    active: false,
                },
            ]),
        }
    }
}

mod model {
    #[derive(
        Debug, Clone, serde::Serialize, serde::Deserialize, reflectapi::Input, reflectapi::Output,
    )]
    pub struct User {
        pub id: u64,
        pub username: String,
        pub email: String,
        pub active: bool,
    }

    #[derive(
        Debug, Clone, serde::Serialize, serde::Deserialize, reflectapi::Input, reflectapi::Output,
    )]
    pub struct Message {
        pub text: String,
        pub timestamp: String,
    }
}

async fn get_message(
    _: Arc<AppState>,
    _request: reflectapi::Empty,
    _headers: reflectapi::Empty,
) -> model::Message {
    model::Message {
        text: "Hello from reflectapi!".to_string(),
        timestamp: "2024-01-01T00:00:00Z".to_string(),
    }
}

async fn create_user(
    state: Arc<AppState>,
    request: proto::CreateUserRequest,
    _headers: reflectapi::Empty,
) -> Result<model::User, proto::CreateUserError> {
    let mut users = state.users.lock().unwrap();

    if request.username.is_empty() {
        return Err(proto::CreateUserError::InvalidInput {
            message: "Username cannot be empty".to_string(),
        });
    }

    if users.iter().any(|u| u.username == request.username) {
        return Err(proto::CreateUserError::UserExists);
    }

    let new_id = users.iter().map(|u| u.id).max().unwrap_or(0) + 1;
    let new_user = model::User {
        id: new_id,
        username: request.username,
        email: request.email,
        active: true,
    };

    users.push(new_user.clone());
    Ok(new_user)
}

async fn get_users(
    state: Arc<AppState>,
    _request: reflectapi::Empty,
    _headers: reflectapi::Empty,
) -> Vec<model::User> {
    let users = state.users.lock().unwrap();
    users.clone()
}

mod proto {
    #[derive(serde::Deserialize, reflectapi::Input)]
    pub struct CreateUserRequest {
        pub username: String,
        pub email: String,
    }

    #[derive(serde::Serialize, reflectapi::Output)]
    pub enum CreateUserError {
        UserExists,
        InvalidInput { message: String },
    }

    impl reflectapi::StatusCode for CreateUserError {
        fn status_code(&self) -> http::StatusCode {
            match self {
                CreateUserError::UserExists => http::StatusCode::CONFLICT,
                CreateUserError::InvalidInput { .. } => http::StatusCode::BAD_REQUEST,
            }
        }
    }
}