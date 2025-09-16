use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[cfg(feature = "utoipa")]
use utoipa::ToSchema;

#[cfg(feature = "reflectapi")]
use reflectapi::{Input, Output};

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Input, Output))]
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Role {
    Admin,
    Editor,
    Viewer,
}

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Input, Output))]
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum AccountStatus {
    Active,
    Invited,
    Suspended,
}

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Input, Output))]
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Theme {
    Light,
    Dark,
    System,
}

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Input, Output))]
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Preferences {
    pub theme: Theme,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub timezone: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[cfg_attr(feature = "utoipa", schema(value_type = String, format = DateTime))]
    pub last_login_at: Option<DateTime<Utc>>,
}

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Input, Output))]
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct User {
    pub id: u64,
    pub username: String,
    // pub display_name: String,
    pub email: String,
    #[cfg_attr(feature = "utoipa", schema(value_type = String, format = DateTime))]
    pub created_at: DateTime<Utc>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub roles: Vec<Role>,
    pub status: AccountStatus,
    pub active: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub preferences: Option<Preferences>,
}

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Input, Output))]
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct HealthStatus {
    pub status: String,
    #[cfg_attr(feature = "utoipa", schema(value_type = String, format = DateTime))]
    pub checked_at: DateTime<Utc>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub region: Option<String>,
}

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Input))]
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct CreateUserRequest {
    pub username: String,
    pub email: String,
    #[serde(default)]
    pub roles: Vec<Role>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub timezone: Option<String>,
}

#[cfg_attr(feature = "utoipa", derive(ToSchema))]
#[cfg_attr(feature = "reflectapi", derive(Output))]
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ApiError {
    pub code: String,
    pub message: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub detail: Option<String>,
}

#[cfg(feature = "reflectapi")]
impl reflectapi::StatusCode for ApiError {
    fn status_code(&self) -> http::StatusCode {
        match self.code.as_str() {
            "user_not_found" => http::StatusCode::NOT_FOUND,
            "invalid_username" | "invalid_email" => http::StatusCode::BAD_REQUEST,
            "user_exists" => http::StatusCode::CONFLICT,
            _ => http::StatusCode::INTERNAL_SERVER_ERROR,
        }
    }
}
