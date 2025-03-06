const redis = require("redis");

let self = module.exports = {
    'container' : null,
    stablish: function() {
        const uri = process.env.REDIS_CONNECTION_URI || 'localhost'
        const port = process.env.REDIS_CONNECTION_PORT || '6379'
    
        self.container = redis.createClient(port, uri,
            {
                retry_strategy: function(options) {
                  if (options.error && options.error.code === "ECONNREFUSED") {
                    // End reconnecting on a specific error and flush all commands with
                    // a individual error
                    return new Error("The server refused the connection");
                  }
                  if (options.total_retry_time > 1000 * 60 * 60) {
                    // End reconnecting after a specific timeout and flush all commands
                    // with a individual error
                    return new Error("Retry time exhausted");
                  }
                  if (options.attempt > 10) {
                    // End reconnecting with built in error
                    return undefined;
                  }
                  // reconnect after
                  return Math.min(options.attempt * 100, 3000);
                },
              }
        );
    
        console.log('Redis Module Connected at ', uri, port)
    }
};

