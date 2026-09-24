(function () {
  'use strict';

  window.NEW_GYM_CONFIG = Object.freeze({
    name: 'New Gym',
    shortName: 'NG',
    city: '',
    phoneDisplay: '',
    phoneHref: '',
    whatsappNumber: '',
    address: '',
    instagramUrl: '',
    memberGatewayBase: '',
    firebase: Object.freeze({
      apiKey: '',
      authDomain: '',
      projectId: '',
      appId: ''
    }),
    analyticsFirebase: Object.freeze({
      apiKey: '',
      authDomain: '',
      projectId: '',
      storageBucket: '',
      messagingSenderId: '',
      appId: '',
      measurementId: ''
    })
  });
})();