use chrono::{Duration, Utc};
use shared_models::{
    AccountStatus, ApiError, CreateUserRequest, HealthStatus, Preferences, Role, Theme, User,
};
use std::sync::{Arc, Mutex};

pub fn builder() -> reflectapi::Builder<Arc<AppState>> {
    reflectapi::Builder::new()
        .name("Reflect API Demo")
        .description("A unified API surface for comparing utoipa and reflectapi")
        .route(get_health, |b| {
            b.name("health.get")
                .readonly(true)
                .tag("health")
                .description("Get server health metadata")
        })
        .route(list_users, |b| {
            b.name("users.list")
                .readonly(true)
                .tag("users")
                .description("List all users with profile metadata")
        })
        .route(get_user, |b| {
            b.name("user.get")
                .tag("users")
                .description("Fetch a single user by id")
        })
        .route(create_user, |b| {
            b.name("user.create")
                .tag("users")
                .description("Create a new user with validation")
        })
}

#[derive(Debug)]
pub struct AppState {
    users: Mutex<Vec<User>>,
}

impl Default for AppState {
    fn default() -> Self {
        let now = Utc::now();
        Self {
            users: Mutex::new(vec![
                User {
                    id: 1,
                    username: "ferris".to_string(),
                    email: "ferris@example.com".to_string(),
                    created_at: now - Duration::days(7),
                    roles: vec![Role::Admin],
                    status: AccountStatus::Active,
                    active: true,
                    preferences: Some(Preferences {
                        theme: Theme::Dark,
                        timezone: Some("America/New_York".to_string()),
                        last_login_at: Some(now - Duration::hours(4)),
                    }),
                },
                User {
                    id: 2,
                    username: "rustacean".to_string(),
                    email: "rustacean@example.com".to_string(),
                    created_at: now - Duration::days(30),
                    roles: vec![Role::Editor, Role::Viewer],
                    status: AccountStatus::Suspended,
                    active: false,
                    preferences: Some(Preferences {
                        theme: Theme::Light,
                        timezone: Some("Europe/Berlin".to_string()),
                        last_login_at: None,
                    }),
                },
            ]),
        }
    }
}

pub async fn get_health(
    _: Arc<AppState>,
    _request: reflectapi::Empty,
    _headers: reflectapi::Empty,
) -> HealthStatus {
    HealthStatus {
        status: "ok".to_string(),
        checked_at: Utc::now(),
        region: Some("us-east-1".to_string()),
    }
}

async fn list_users(
    state: Arc<AppState>,
    _request: reflectapi::Empty,
    _headers: reflectapi::Empty,
) -> Vec<User> {
    state.users.lock().unwrap().clone()
}

#[derive(serde::Deserialize, reflectapi::Input)]
pub struct GetUserRequest {
    pub id: u64,
}

pub async fn get_user(
    state: Arc<AppState>,
    request: GetUserRequest,
    _headers: reflectapi::Empty,
) -> Result<User, ApiError> {
    state
        .users
        .lock()
        .unwrap()
        .iter()
        .find(|user| user.id == request.id)
        .cloned()
        .ok_or_else(|| ApiError {
            code: "user_not_found".to_string(),
            message: format!("No user with id {}", request.id),
            detail: None,
        })
}

async fn create_user(
    state: Arc<AppState>,
    request: CreateUserRequest,
    _headers: reflectapi::Empty,
) -> Result<User, ApiError> {
    if request.username.trim().is_empty() {
        return Err(ApiError {
            code: "invalid_username".to_string(),
            message: "Username must not be empty".to_string(),
            detail: Some("Provide a non-empty username".to_string()),
        });
    }

    if !request.email.contains('@') {
        return Err(ApiError {
            code: "invalid_email".to_string(),
            message: "Email address must contain '@'".to_string(),
            detail: Some("Example: user@example.com".to_string()),
        });
    }

    let mut users = state.users.lock().unwrap();

    if users
        .iter()
        .any(|user| user.username.eq_ignore_ascii_case(&request.username))
    {
        return Err(ApiError {
            code: "user_exists".to_string(),
            message: format!("A user named '{}' already exists", request.username),
            detail: None,
        });
    }

    let new_id = users.iter().map(|user| user.id).max().unwrap_or(0) + 1;
    let roles = if request.roles.is_empty() {
        vec![Role::Viewer]
    } else {
        request.roles.clone()
    };

    let new_user = User {
        id: new_id,
        username: request.username.trim().to_string(),
        email: request.email.trim().to_string(),
        created_at: Utc::now(),
        roles,
        status: AccountStatus::Invited,
        active: true,
        preferences: Some(Preferences {
            theme: Theme::System,
            timezone: request.timezone.clone(),
            last_login_at: None,
        }),
    };

    users.push(new_user.clone());
    Ok(new_user)
}
