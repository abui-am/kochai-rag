# Google OAuth2 Authentication Setup Guide

This guide explains how to set up Google OAuth2 authentication for the Fitness RAG API.

## Prerequisites

1. **Google Cloud Console Account**: You need a Google Cloud Platform account
2. **Project Setup**: Create a new project or use an existing one
3. **Domain**: You need a domain for production use

## Step 1: Create Google OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Navigate to **APIs & Services > Credentials**
4. Click **Create Credentials > OAuth 2.0 Client IDs**
5. Choose **Web application**
6. Configure the OAuth consent screen if prompted

## Step 2: Configure OAuth2 Settings

In the OAuth 2.0 Client IDs creation form:

1. **Name**: Give your client a name (e.g., "Fitness RAG API")
2. **Authorized JavaScript origins**:
   - For development: `http://localhost:8000`
   - For production: `https://yourdomain.com`
3. **Authorized redirect URIs**:
   - For development: `http://localhost:8000/auth/google/callback`
   - For production: `https://yourdomain.com/auth/google/callback`

## Step 3: Get Your Credentials

After creating the OAuth 2.0 client, you'll get:

- **Client ID**: `your_google_client_id_here`
- **Client Secret**: `your_google_client_secret_here`

## Step 4: Update Environment Variables

Edit the `.env` file in your project root:

```bash
# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=your_actual_google_client_id_here
GOOGLE_CLIENT_SECRET=your_actual_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# For production, update the redirect URI:
# GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/google/callback
```

## Step 5: Enable Required APIs

In Google Cloud Console:

1. Go to **APIs & Services > Library**
2. Enable the following APIs:
   - **Google+ API** (for user profile information)
   - **Google OAuth2 API** (usually enabled by default)

## Step 6: Test the Setup

1. **Start the API server**:

   ```bash
   cd /path/to/fitness-rag
   python run.py
   ```

2. **Test authentication endpoints**:

   - **Get auth status**: `GET /auth/status`
   - **Initiate login**: `GET /auth/login` (redirects to Google)
   - **Get user info**: `GET /auth/me` (requires authentication)

3. **Test protected endpoints**:
   - **Query (protected)**: `POST /query` (requires authentication)
   - **Vanilla GPT comparison**: `POST /query/vanilla` (uses the same JWT if provided)

### Vanilla GPT Comparison Endpoint

Use this endpoint to compare RAG answers with a plain GPT response.  
The OpenAI Responses API is called directly—no PaperQA retrieval is performed.

- **URL**: `POST /query/vanilla`
- **Headers**:
  - `Content-Type: application/json`
  - `Authorization: Bearer <JWT>` (optional, enables preference injection)
- **JSON payload (required)**:

```json
{
  "text": "Apa manfaat compound exercise buat muscle growth?"
}
```

- **Response**:

```json
{
  "answer": "Latihan compound seperti squat membantu kamu melibatkan banyak kelompok otot ...",
  "model": "gpt-4o-mini",
  "usage": {
    "input_tokens": 315,
    "output_tokens": 185,
    "total_tokens": 500
  },
  "query": "Apa manfaat compound exercise buat muscle growth?",
  "status": "success",
  "preferences": "- Name: Raka\n- Fitness goals: muscle_gain"
}
```

> Use this output to benchmark latency, cost, or tone differences against the PaperQA-powered `/query` endpoint. Preferences are derived automatically from the authenticated user profile (if available).

## Authentication Flow

### 1. Login Process

1. User visits `/auth/login`
2. API redirects to Google OAuth2 authorization URL
3. User authenticates with Google
4. Google redirects to `/auth/google/callback` with auth code
5. API exchanges code for access token
6. API fetches user info from Google
7. API creates JWT token for session
8. API redirects to frontend with JWT token

### 2. Protected Route Access

1. Client includes JWT token in `Authorization: Bearer <token>` header
2. API validates JWT token
3. If valid, user can access protected endpoints
4. If invalid, API returns 401 Unauthorized

### 3. Logout Process

1. Client calls `POST /auth/logout`
2. API invalidates user session (in production, use database/cache)

## Security Notes

- **JWT Secret**: Change the `JWT_SECRET_KEY` in `.env` to a strong random string
- **HTTPS Required**: Use HTTPS in production for secure token transmission
- **Token Expiration**: Current setup uses 30-minute token expiration
- **State Parameter**: The implementation includes CSRF protection with state parameter

## Production Deployment

For production deployment:

1. Use a strong, randomly generated `JWT_SECRET_KEY`
2. Set `GOOGLE_REDIRECT_URI` to your production domain
3. Use HTTPS for all communications
4. Store user sessions in a database or Redis cache
5. Implement rate limiting on authentication endpoints
6. Monitor authentication logs for security events

## Troubleshooting

### Common Issues

1. **Invalid client**: Check that your Google Client ID and Secret are correct
2. **Redirect URI mismatch**: Ensure redirect URI matches exactly in Google Console
3. **CORS errors**: Add your frontend domain to CORS origins in main.py
4. **Token validation errors**: Check JWT_SECRET_KEY is set correctly

### Debug Endpoints

- `/auth/status` - Check authentication status
- `/auth/me` - Get current user info (requires auth)
- `/` - Health check endpoint

## API Endpoints Summary

| Endpoint                | Method | Description                  | Auth Required  |
| ----------------------- | ------ | ---------------------------- | -------------- |
| `/auth/login`           | GET    | Initiate Google OAuth2 login | No             |
| `/auth/google/callback` | GET    | Handle OAuth2 callback       | No             |
| `/auth/logout`          | POST   | Logout user                  | Yes            |
| `/auth/me`              | GET    | Get current user info        | Yes            |
| `/auth/status`          | GET    | Get auth status              | No             |
| `/query`                | POST   | Query knowledge base         | Yes            |
| `/query/vanilla`        | POST   | GPT-only comparison query    | Yes (optional) |
| `/system/status`        | GET    | Get system status            | No             |

## Next Steps

After setting up Google OAuth2:

1. Implement user session storage (database/Redis)
2. Add user registration and profile management
3. Implement role-based access control if needed
4. Add OAuth2 refresh token handling
5. Set up proper logging and monitoring
