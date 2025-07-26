import { createBrowserRouter, Navigate } from 'react-router-dom'
import { RootLayout } from './components/layouts/RootLayout'
import { ProtectedLayout } from './components/layouts/ProtectedLayout'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { CatalogsPage } from './pages/CatalogsPage'
import { CatalogDetailPage } from './pages/CatalogDetailPage'
import { MediaDetailPage } from './pages/MediaDetailPage'
import { SearchPage } from './pages/SearchPage'
import { UploadPage } from './pages/UploadPage'
import { SettingsPage } from './pages/SettingsPage'
import { NotFoundPage } from './pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/catalogs" replace />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      {
        element: <ProtectedLayout />,
        children: [
          {
            path: 'catalogs',
            element: <CatalogsPage />,
          },
          {
            path: 'catalogs/:catalogId',
            element: <CatalogDetailPage />,
          },
          {
            path: 'catalogs/:catalogId/upload',
            element: <UploadPage />,
          },
          {
            path: 'media/:mediaId',
            element: <MediaDetailPage />,
          },
          {
            path: 'search',
            element: <SearchPage />,
          },
          {
            path: 'settings',
            element: <SettingsPage />,
          },
        ],
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
])
