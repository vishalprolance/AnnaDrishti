import { useEffect, useState } from 'react';
import { DEMO_DATA } from '../config';

interface Message {
  id: string;
  sender: 'agent' | 'buyer';
  message: string;
  price?: number;
  timestamp: string;
}

interface NegotiationChatProps {
  workflowId: string | null;
}

export default function NegotiationChat({ workflowId }: NegotiationChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    if (!workflowId) {
      setMessages([]);
      return;
    }

    // Simulate negotiation messages
    const timer = setTimeout(() => {
      setMessages([
        {
          id: '1',
          sender: 'agent',
          message: `Hello! I represent Ramesh Patil. We have 2,300 kg of premium tomatoes. Based on current market rates, I'm offering at ₹${DEMO_DATA.negotiation.initial_offer}/kg.`,
          price: DEMO_DATA.negotiation.initial_offer,
          timestamp: new Date().toISOString(),
        },
      ]);
    }, 7000);

    const timer2 = setTimeout(() => {
      setMessages(prev => [
        ...prev,
        {
          id: '2',
          sender: 'buyer',
          message: `The quality looks good, but ₹${DEMO_DATA.negotiation.buyer_response}/kg is the best I can do given transport costs.`,
          price: DEMO_DATA.negotiation.buyer_response,
          timestamp: new Date().toISOString(),
        },
      ]);
    }, 10000);

    const timer3 = setTimeout(() => {
      setMessages(prev => [
        ...prev,
        {
          id: '3',
          sender: 'agent',
          message: `I understand your concerns. Considering the premium quality and harvest freshness, I can offer ₹${DEMO_DATA.negotiation.counter_offer}/kg. This is a fair price for both parties.`,
          price: DEMO_DATA.negotiation.counter_offer,
          timestamp: new Date().toISOString(),
        },
      ]);
    }, 13000);

    const timer4 = setTimeout(() => {
      setMessages(prev => [
        ...prev,
        {
          id: '4',
          sender: 'buyer',
          message: `Deal! ₹${DEMO_DATA.negotiation.final_price}/kg works for me. I'll take the full quantity.`,
          price: DEMO_DATA.negotiation.final_price,
          timestamp: new Date().toISOString(),
        },
      ]);
    }, 16000);

    return () => {
      clearTimeout(timer);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
    };
  }, [workflowId]);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">AI Negotiation</h2>
        <p className="text-sm text-gray-600 mt-1">
          Powered by Claude 4.5 Haiku
          <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-800 text-xs font-medium rounded">
            LIVE AI
          </span>
        </p>
      </div>

      <div className="p-4 space-y-4 max-h-[400px] overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>Waiting for negotiation to start...</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === 'agent' ? 'justify-start' : 'justify-end'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  msg.sender === 'agent'
                    ? 'bg-blue-50 border border-blue-200'
                    : 'bg-green-50 border border-green-200'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-xs font-medium text-gray-700">
                    {msg.sender === 'agent' ? '🤖 AI Agent' : '👤 Buyer'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-sm text-gray-900">{msg.message}</p>
                {msg.price && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <span className="text-lg font-bold text-gray-900">₹{msg.price}/kg</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {messages.length > 0 && messages[messages.length - 1].sender === 'buyer' && messages[messages.length - 1].message.includes('Deal') && (
        <div className="p-4 bg-green-50 border-t border-green-200">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🎉</span>
            <div>
              <p className="text-sm font-medium text-green-900">Deal Closed!</p>
              <p className="text-xs text-green-700">Final price: ₹{DEMO_DATA.negotiation.final_price}/kg</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
