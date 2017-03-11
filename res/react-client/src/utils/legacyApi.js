function _encodeFormData (data) {
  return (
      Object.keys(data)
      .map((objKey) => {
        return objKey + '=' + data[objKey];
      })
      .join('&')
  );
}

export function legacyAPICall (endpoint, data, authtoken) {
  return new Promise((resolve, reject) => {
    const params = {
      data: encodeURIComponent(JSON.stringify(data)),
    };
    if (typeof authtoken !== 'undefined') {
      params['authtoken'] = authtoken;
    }
    fetch(
        endpoint,
      {
        credentials: 'include',
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
        body: _encodeFormData(params),
      }
      ).then(
        (response) => {
          if (response.status >= 400 && response.status <= 599) {
            console.log(
              'Could not fetch ' + endpoint + ' got HTTP ' + response.status
            );
            reject(response);
            return;
          }
          response.json().then(
            (content) => { resolve(content.data); },
            () => {
              console.log('Could not decode json: ' + endpoint);
              reject('Error decoding json.');
            }
          );
        },
        (error) => {
          console.log(error);
          // fetch considers any http response as success, so if we get here
          // the request itself did not work!
          reject('CONNECTION_ERROR');
        }
      );
  });
}

export function postForm (endpoint, data) {
  return new Promise((resolve, reject) => {
    const params = {
      credentials: 'include',
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    };
    if (typeof data !== 'undefined') {
      params.body = (
                Object.keys(data)
                .map((objKey) => {
                  return objKey + '=' + encodeURIComponent(data[objKey]);
                })
                .join('&')
            );
    }

    fetch(endpoint, params)
        .then((response) => {
          if (response.status >= 400 && response.status <= 599) {
            reject(response);
            return;
          }
          resolve(response);
        })
        .catch((error) => { reject(error); });
  });
}
