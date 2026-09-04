import React, { useState, useEffect, useRef } from 'react';

export default function PodcastPlayer({ article, analysis }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  
  const synthRef = useRef(null);
  const utteranceRef = useRef(null);

  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setIsSupported(false);
      return;
    }
    synthRef.current = window.speechSynthesis;
    
    // Stop playing when component unmounts
    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  const generateScript = () => {
    const lang = analysis.language_code === 'en' ? 'en-US' : 'id-ID';
    
    let text = "";
    if (lang === 'en-US') {
      text = `News update: ${article.title}. `;
      
      const sentiment = analysis.sentiment || "Neutral";
      text += `Our AI detects that this news has a ${sentiment.toLowerCase()} tone. `;
      
      const firstPara = article.content?.split('\n')[0] || '';
      if (firstPara) {
        text += `Here is an excerpt from the article: ${firstPara.slice(0, 300)}...`;
      }
    } else {
      text = `Berita hari ini: ${article.title}. `;
      
      let sent = analysis.sentiment || "Netral";
      if (sent.toLowerCase() === 'positive') sent = "positif";
      if (sent.toLowerCase() === 'negative') sent = "negatif";
      
      text += `Hasil analisis kami menunjukkan berita ini memiliki sentimen ${sent}. `;
      
      const firstPara = article.content?.split('\n').find(p => p.trim().length > 20) || '';
      if (firstPara) {
        text += `Berikut adalah kutipan beritanya: ${firstPara.slice(0, 400)}...`;
      }
    }
    return { text, lang };
  };

  const handlePlay = () => {
    if (!synthRef.current) return;
    
    if (isPaused) {
      synthRef.current.resume();
      setIsPaused(false);
      setIsPlaying(true);
      return;
    }

    const { text, lang } = generateScript();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      setIsPlaying(false);
      setIsPaused(false);
    };
    
    utterance.onerror = (e) => {
      console.error('Speech synthesis error', e);
      setIsPlaying(false);
      setIsPaused(false);
    };

    utteranceRef.current = utterance;
    
    // Cancel any previous speech
    synthRef.current.cancel();
    
    synthRef.current.speak(utterance);
    setIsPlaying(true);
    setIsPaused(false);
  };

  const handlePause = () => {
    if (!synthRef.current) return;
    synthRef.current.pause();
    setIsPaused(true);
    setIsPlaying(false);
  };

  const handleStop = () => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  };

  if (!isSupported) return null;

  return (
    <div className="podcast-player hide-on-print">
      <div className="podcast-label">
        <span className="podcast-icon">🔊</span>
        Siaran Berita
      </div>
      <div className="podcast-controls">
        {!isPlaying ? (
          <button onClick={handlePlay} className="podcast-btn play-btn" aria-label="Play">
            ▶ Putar
          </button>
        ) : (
          <button onClick={handlePause} className="podcast-btn pause-btn" aria-label="Pause">
            ⏸ Jeda
          </button>
        )}
        {(isPlaying || isPaused) && (
          <button onClick={handleStop} className="podcast-btn stop-btn" aria-label="Stop">
            ⏹ Berhenti
          </button>
        )}
      </div>
    </div>
  );
}
