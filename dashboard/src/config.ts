export const API_URL = import.meta.env.VITE_API_URL || 'https://35t4gu37d5.execute-api.ap-south-1.amazonaws.com/demo';

export const DEMO_DATA = {
  farmerInput: {
    farmer_name: 'Ramesh Patil',
    crop_type: 'tomato',
    plot_area: 2.1,
    estimated_quantity: 2300,
    location: 'Sinnar, Nashik',
  },
  marketPrices: [
    { mandi: 'Sinnar', price: 26, transport: 0.5, net_price: 25.5 },
    { mandi: 'Nashik', price: 27, transport: 1.2, net_price: 25.8 },
    { mandi: 'Pune', price: 28, transport: 3.5, net_price: 24.5 },
    { mandi: 'Mumbai', price: 30, transport: 5.0, net_price: 25.0 },
  ],
  surplus: {
    total_volume: 32000,
    mandi_capacity: 22000,
    surplus: 10000,
    fresh_allocation: 22000,
    processing_allocation: 10000,
  },
  processors: [
    { name: 'Sai Agro Processing', capacity: 5000, rate: 32 },
    { name: 'Krishi Processing Unit', capacity: 2000, rate: 38 },
    { name: 'Maharashtra Food Corp', capacity: 3000, rate: 30 },
  ],
  negotiation: {
    initial_offer: 26.5,
    buyer_response: 24.5,
    counter_offer: 27.5,
    final_price: 27.5,
    floor_price: 24.0,
  },
};
