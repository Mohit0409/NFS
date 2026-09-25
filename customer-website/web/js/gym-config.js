(function () {
  'use strict';

  window.NEW_GYM_CONFIG = Object.freeze({
    name: 'Need For Strength',
    shortName: 'NFS',
    city: 'Neemuch',
    phoneDisplay: '+91 98937 04372',
    phoneHref: 'tel:+919893704372',
    whatsappNumber: '919893704372',
    address: 'Opposite Pachvati Colony, Near Nakoda Dham Temple, Neemuch, Madhya Pradesh',
    openingHours: '6:00 AM – 10:00 PM daily (demo timing)',
    openingAnnouncement: 'Grand Opening · November 2026 · Neemuch',
    foundingOfferText: 'Founding 100 Members Offer · Limited Slots',
    instagramUrl: 'https://instagram.com/needforstrength',
    mapUrl: 'https://www.google.com/maps/search/?api=1&query=Need+For+Strength+Near+Nakoda+Dham+Temple+Neemuch',
    mapEmbedUrl: 'https://www.google.com/maps?q=Need+For+Strength+Near+Nakoda+Dham+Temple+Neemuch&output=embed',
    siteUrl: '',
    memberGatewayBase: '',
    poolName: 'The Cue Master',
    poolDemoRatesPaise: Object.freeze({
      private: 30000,
      common: 20000
    }),
    membershipPricesPaise: Object.freeze({
      trial: null,
      oneMonth: 249900,
      threeMonths: 600000,
      oneYear: 2400000
    }),
    membershipOffers: Object.freeze([
      Object.freeze({
        title: 'Women Membership',
        badge: 'Founding 100 Members',
        featured: true,
        lines: Object.freeze([
          Object.freeze({ label: '12 Months', price: '₹21,999', note: 'Founding offer' }),
          Object.freeze({ label: 'Regular 1 Month', price: '₹2,499' }),
          Object.freeze({ label: 'Regular 3 Months', price: '₹6,000' }),
          Object.freeze({ label: 'Regular 6 Months', price: '₹10,800' }),
          Object.freeze({ label: 'Regular 12 Months', price: '₹24,000' })
        ])
      }),
      Object.freeze({
        title: 'Men Membership',
        badge: 'Founding 100 Members',
        featured: true,
        lines: Object.freeze([
          Object.freeze({ label: '12 Months', price: '₹27,999', note: 'Founding offer' }),
          Object.freeze({ label: 'Regular 1 Month', price: '₹2,999' }),
          Object.freeze({ label: 'Regular 3 Months', price: '₹7,500' }),
          Object.freeze({ label: 'Regular 6 Months', price: '₹13,500' }),
          Object.freeze({ label: 'Regular 12 Months', price: '₹30,000' })
        ])
      }),
      Object.freeze({
        title: 'Student Membership',
        badge: 'Valid Student ID Required',
        lines: Object.freeze([
          Object.freeze({ label: '1 Month', price: '₹1,999' }),
          Object.freeze({ label: '3 Months', price: '₹5,499' }),
          Object.freeze({ label: '6 Months', price: '₹9,999' })
        ])
      }),
      Object.freeze({
        title: 'Couple Membership',
        badge: 'Train Together',
        lines: Object.freeze([
          Object.freeze({ label: '3 Months', price: '₹11,000' }),
          Object.freeze({ label: '6 Months', price: '₹20,000' }),
          Object.freeze({ label: '12 Months', price: '₹48,000' })
        ])
      })
    ]),
    personalTrainingOffers: Object.freeze([
      Object.freeze({ label: '1 Month · 8 Sessions', price: '₹3,999' }),
      Object.freeze({ label: '1 Month · 12 Sessions', price: '₹5,499' }),
      Object.freeze({ label: '1 Month · 16 Sessions', price: '₹6,999' }),
      Object.freeze({ label: '3 Months · 24 Sessions', price: '₹10,999' }),
      Object.freeze({ label: '3 Months · 36 Sessions', price: '₹15,999' })
    ]),
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
