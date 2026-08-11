import { Endpoints, userAgents, ApiContextEnum } from './constants.js'

type EndpointValue = string

interface FetchParams {
  endpoint: EndpointValue
  params: Record<string, string | number>
  context?: ApiContextEnum
}

interface FetchResponse<T> {
  data: T
  ok: boolean
}

export const useFetch = async <T>({ endpoint, params, context }: FetchParams): Promise<FetchResponse<T>> => {
  const url = new URL('https://www.jiosaavn.com/api.php')

  url.searchParams.append('__call', endpoint.toString())
  url.searchParams.append('_format', 'json')
  url.searchParams.append('_marker', '0')
  url.searchParams.append('api_version', '4')
  url.searchParams.append('ctx', context || ApiContextEnum.WEB6DOT0)

  Object.keys(params).forEach((key) => url.searchParams.append(key, String(params[key])))

  const randomUserAgent = userAgents[Math.floor(Math.random() * userAgents.length)]

  const response = await fetch(url.toString(), {
    headers: { 'Content-Type': 'application/json', 'User-Agent': randomUserAgent }
  })

  const data = await response.json() as T

  return { data, ok: response.ok }
}
