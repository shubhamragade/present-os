import { Layout } from './components/layout/Layout';
import { ChatArea } from './components/chat/ChatArea';
import { InputBar } from './components/input/InputBar';

function App() {
  return (
    <Layout>
      <div className="flex flex-col h-full max-w-4xl mx-auto w-full relative">
        <ChatArea />
        <InputBar />
      </div>
    </Layout>
  );
}

export default App;
