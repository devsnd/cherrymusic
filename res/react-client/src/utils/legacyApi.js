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
        data: encodeURIComponent(JSON.stringify(data))
      };
      if (typeof authtoken !== 'undefined') {
        params['authtoken'] = authtoken;
      }
      fetch(
        endpoint,
        {
          credentials: 'include',
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: _encodeFormData(params)
        }
      )
        .then((response) => {
          if (response.status >= 400 && response.status <= 599) {
            reject(response);
            return;
          }
          response.json().then(
            (content) => { resolve(content.data);              },
            () => { reject('Error decoding json.'); }
          );
        })
        .catch((error) => { reject(error); });
    });
}

export function postForm (endpoint, data) {
    return new Promise((resolve, reject) => {
        const params = {
            credentials: 'include',
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        }
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
