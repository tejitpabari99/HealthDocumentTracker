# API Configuration

This directory contains the API configuration for connecting the frontend to the backend.

## Changing the API Host

The application is currently configured to connect to `http://localhost:5000` for local development.

### When Deploying to Production

1. **Open `Frontend/config/api.ts`**

2. **Update the `API_HOST` constant** on line 6:

```typescript
// Change from:
const API_HOST = 'http://localhost:5000';

// To your deployed backend URL:
const API_HOST = 'https://your-backend-domain.com';
```

### Examples

**Azure App Service:**
```typescript
const API_HOST = 'https://health-doc-tracker.azurewebsites.net';
```

**AWS Elastic Beanstalk:**
```typescript
const API_HOST = 'https://health-doc-api.us-east-1.elasticbeanstalk.com';
```

**Heroku:**
```typescript
const API_HOST = 'https://health-doc-tracker.herokuapp.com';
```

**Custom Domain:**
```typescript
const API_HOST = 'https://api.healthdoctracker.com';
```

### Testing the Connection

After updating the host, you can test the connection by:

1. Starting the frontend app: `npm start`
2. Trying to upload a document or search
3. Check the console for any connection errors

### Important Notes

- ✅ Always use `https://` in production (not `http://`)
- ✅ Do not include trailing slashes in the URL
- ✅ Make sure your backend allows CORS from your frontend domain
- ✅ Ensure your backend is running and accessible at the specified URL

## API Endpoints

The following endpoints are available:

- **POST** `/documents` - Upload a single document
- **POST** `/documents/search` - Search documents with a query
- **GET** `/health` - Backend health check

## Future Enhancement

For a more robust solution, consider:

1. **Environment Variables**: Use `.env` files with different configurations for dev/prod
2. **AsyncStorage**: Save the API host in local storage for runtime configuration
3. **Config Screen**: Add a settings screen where users can update the API host
