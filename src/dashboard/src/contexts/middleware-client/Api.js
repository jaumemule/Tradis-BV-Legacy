import axios from 'axios';
import { runtimeConfig } from '../../../src/config';

class Api {
  constructor() {
    this.axiosInstance = axios.create({
      retry: 5,
      headers: {
        common: {
          'Content-Type': 'application/json',
          'client-id': 'coolId',
          'client-secret': 'coolSecret',
        },
      },
      baseURL: `${runtimeConfig.MIDDLEWARE_URl}/api/v1`,
    });
  }

  set apiToken(apiToken) {
    if (apiToken) {
      this.axiosInstance.defaults.headers.Authorization = `Bearer ${apiToken}`;
    } else {
      delete this.axiosInstance.defaults.headers.Authorization;
    }
  }

  get(url, config) {
    return this.axiosInstance.get(url, config);
  }

  delete(url, config) {
    return this.axiosInstance.delete(url, config);
  }

  post(url, data, config) {
    return this.axiosInstance.post(url, data, config);
  }

  put(url, data, config) {
    return this.axiosInstance.put(url, data, config);
  }

  patch(url, data, config) {
    return this.axiosInstance.patch(url, data, config);
  }
}

export default Api;
