export const runtimeConfig =
  typeof window !== 'undefined'
    ? {
        // client
        MIDDLEWARE_URl: window.env.MIDDLEWARE_URl,
      }
    : {
        // server
        MIDDLEWARE_URl: process.env.MIDDLEWARE_URl,
      };
