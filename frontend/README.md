# Apollonia Frontend

Modern React-based web interface for the Apollonia media catalog system.

## Features

- **Authentication**: JWT-based authentication with secure token management
- **Media Management**: Upload, browse, and organize media files
- **Real-time Processing**: Track file processing status in real-time
- **Analytics Dashboard**: Visualize storage usage, processing metrics, and trends
- **Responsive Design**: Mobile-first design with dark mode support
- **GraphQL & REST**: Dual API support with Apollo Client and Axios

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and optimized builds
- **TailwindCSS** for styling
- **Zustand** for state management
- **Apollo Client** for GraphQL
- **Tanstack Query** for REST API caching
- **React Router** for navigation
- **Recharts** for data visualization
- **React Hook Form** for form handling

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Environment Variables

Create a `.env.local` file:

```env
VITE_API_URL=http://localhost:8000
VITE_GRAPHQL_URL=http://localhost:8000/graphql
```

## Project Structure

```
src/
├── components/       # Reusable UI components
│   ├── layouts/     # Page layouts
│   └── ui/          # Core UI elements
├── pages/           # Route pages
├── services/        # API clients
├── stores/          # Zustand stores
├── hooks/           # Custom React hooks
├── utils/           # Utility functions
└── types/           # TypeScript types
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run lint` - Lint code
- `npm run format` - Format code with Prettier
- `npm run type-check` - Run TypeScript type checking

## Key Components

### Pages

- **LoginPage**: User authentication
- **HomePage**: Dashboard with analytics overview
- **CatalogsPage**: Browse and manage media catalogs
- **UploadPage**: Drag-and-drop file upload interface
- **AnalyticsPage**: Detailed analytics and visualizations
- **SettingsPage**: User and application settings

### Core Features

1. **File Upload**

   - Drag-and-drop interface
   - Progress tracking
   - Batch upload support
   - Format validation

1. **Media Browser**

   - Grid and list views
   - Search and filtering
   - Metadata display
   - Batch operations

1. **Analytics**

   - Storage usage charts
   - Processing metrics
   - Media type distribution
   - Historical trends

1. **Real-time Updates**

   - WebSocket support (planned)
   - Processing status updates
   - Live notifications

## Development

### Code Style

- TypeScript strict mode enabled
- ESLint + Prettier for formatting
- Component-first architecture
- Hooks for business logic

### Testing

```bash
# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Open test UI
npm run test:ui
```

### Building

```bash
# Development build
npm run build

# Production build with optimizations
npm run build -- --mode production

# Analyze bundle size
npm run build -- --analyze
```

## Deployment

The frontend is designed to be deployed as a static site:

1. Build the production bundle: `npm run build`
1. Deploy the `dist` directory to your hosting service
1. Configure your web server to serve `index.html` for all routes (SPA)

### Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
```

## API Integration

### REST API

```typescript
import { api } from '@/services/api'

// Authenticated request
const response = await api.get('/media/files')
```

### GraphQL

```typescript
import { gql, useQuery } from '@apollo/client'

const GET_FILES = gql`
  query GetFiles {
    files {
      id
      filename
      mediaType
    }
  }
`

const { data, loading } = useQuery(GET_FILES)
```

## Contributing

1. Fork the repository
1. Create a feature branch
1. Commit your changes
1. Push to the branch
1. Create a Pull Request

## License

MIT License - see LICENSE file for details
