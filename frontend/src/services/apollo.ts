import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client'
import { setContext } from '@apollo/client/link/context'

const httpLink = createHttpLink({
  uri: '/graphql',
})

const authLink = setContext((_, { headers }) => {
  // Get the authentication token from zustand store
  const token = localStorage.getItem('auth-storage')

  if (token) {
    try {
      const parsed = JSON.parse(token)
      return {
        headers: {
          ...headers,
          authorization: parsed.state?.token ? `Bearer ${parsed.state.token}` : '',
        },
      }
    } catch (_e) {
      return { headers }
    }
  }

  return { headers }
})

export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
})
