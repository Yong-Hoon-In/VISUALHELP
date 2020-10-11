package com.example.visualhelper;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.AudioManager;
import android.media.ToneGenerator;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Locale;

import static android.net.wifi.p2p.WifiP2pManager.ERROR;

public class MainActivity extends AppCompatActivity {
    private static final String TAG = "result";
    TextView resultText, resultText2, resultTextstt;
    //beep
    ToneGenerator toneGenerator;
    //tts/stt
    private TextToSpeech tts;
    static private String ttsdata;
    static private String sttdata = "";

    Data data = new Data();

    Button ttsButton, sttButton;

    Intent SttIntent;
    SpeechRecognizer mRecognizer;

    //소켓통신
    Handler mHandler, mHandler2;
    Handler handler = new Handler();

    private Socket socket, socket2;

    private DataOutputStream dos, dos2, tsdos;
    private DataInputStream dis, dis2, tsdis;

    private String ip2 = "192.168.1.83";            // IP 번호
    private int port2 = 10035;                          // port 번호
    private String ip = "192.168.1.24";            // IP 번호
    private int port = 10013;                            // port 번호
    final int PERMISSION = 1;

    private static double longitude;
    private static double latitude;
    Context context;
    Button connect_btn;
    Button connect_btn2;
    Button mode, mode2, connect, modeclose, modeclose2, sendemail, sttstart;
    EditText email, getport1, getport2;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        if (Build.VERSION.SDK_INT >= 23) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.INTERNET, Manifest.permission.RECORD_AUDIO}, PERMISSION);
        }
        final LocationManager lm = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        final LocationListener gpsLocationListener = new LocationListener() {
            @Override
            public void onLocationChanged(Location location) {
                longitude = location.getLongitude();
                latitude = location.getLatitude();
                Log.d(TAG, "onLocationChanged: " + longitude + "/" + latitude);
            }

            @Override
            public void onStatusChanged(String provider, int status, Bundle extras) {

            }

            @Override
            public void onProviderEnabled(String provider) {

            }

            @Override
            public void onProviderDisabled(String provider) {

            }
        };
        if (Build.VERSION.SDK_INT >= 23 &&
                ContextCompat.checkSelfPermission(getApplicationContext(), android.Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(MainActivity.this, new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION},
                    0);
        } else {
            lm.requestLocationUpdates(LocationManager.GPS_PROVIDER,
                    1000,
                    1,
                    gpsLocationListener);
            lm.requestLocationUpdates(LocationManager.NETWORK_PROVIDER,
                    1000,
                    1,
                    gpsLocationListener);
        }


        SttIntent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        SttIntent.putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, getPackageName());
        SttIntent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "ko-KR");


        sttstart = findViewById(R.id.startstt);
        sttstart.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                tts.speak("원하시는 기능 말해주세요", TextToSpeech.QUEUE_FLUSH, null);
                mRecognizer = SpeechRecognizer.createSpeechRecognizer(MainActivity.this);
                mRecognizer.setRecognitionListener(listener);
                mRecognizer.startListening(SttIntent);
                if (sttdata.equals("시작")) {
                    connect();
                    handler.postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            connect2();
                        }
                    }, 3000);
                }
                if (sttdata.equals("보호자모드")) {
                    Intent intent = new Intent(MainActivity.this, MapsActivity.class);
                    intent.putExtra("lat", latitude);
                    intent.putExtra("lon", longitude);
                    startActivity(intent);
                }
            }
        });

        //beep
        toneGenerator = new ToneGenerator(AudioManager.STREAM_ALARM, 500);

        tts = new TextToSpeech(this, new TextToSpeech.OnInitListener() {
            @Override
            public void onInit(int status) {
                if (status != ERROR) {
                    // 언어를 선택한다.
                    tts.setLanguage(Locale.KOREAN);
                }
            }
        });


        mode = findViewById(R.id.mode);
        mode.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                connect();
            }
        });
        modeclose = findViewById(R.id.modeclose);
        modeclose.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Log.d(TAG, "onClick: " + data.getOnoff());
                try {
                    dos.write(99);
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        });
        modeclose2 = findViewById(R.id.modeclose2);
        modeclose2.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                data.setOnoff(1);
            }
        });

        mode2 = findViewById(R.id.mode2);
        mode2.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                connect2();
            }
        });

        connect = findViewById(R.id.connect);
        connect.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Intent intent = new Intent(MainActivity.this, MapsActivity.class);

                intent.putExtra("lat", latitude);
                intent.putExtra("lon", longitude);

                startActivity(intent);
            }
        });


        email = findViewById(R.id.email);
        sendemail = findViewById(R.id.sendEmail);
        sendemail.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                try {
                    dos = new DataOutputStream(socket.getOutputStream());
                    dos.writeUTF("guswns2811@naver.com");
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        });
        getport1 = findViewById(R.id.getport);
        getport2 = findViewById(R.id.getport2);
    }

    void connect() {
//        int realport = 0;
//        if(getport1.getText().toString().equals(""))
//        {
//            realport = port;
//        }else realport = (int)getport1.getText().toString()
        mHandler = new Handler();
        Log.w("connect", "연결 하는중");
        // 받아오는거
        Thread checkUpdate = new Thread() {
            public void run() {
                String a = getport1.getText().toString();
                int b = Integer.parseInt(a);
                Log.d(TAG, "run: " + b);
                // 서버 접속
                try {
                    socket = new Socket(ip,b);
                    tts.speak("서버와 접속되었습니다", TextToSpeech.QUEUE_FLUSH, null);
                    Log.w("서버 접속됨", "서버 접속됨");
                } catch (IOException e1) {
                    tts.speak("서버와 접속하지 못했습니다", TextToSpeech.QUEUE_FLUSH, null);
                    Log.w("서버접속못함", "서버접속못함");
                    try {
                        socket.close();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    e1.printStackTrace();
                }

                Log.w("edit 넘어가야 할 값 : ", "안드로이드에서 서버로 연결요청");

                try {
                    dos = new DataOutputStream(socket.getOutputStream());   // output에 보낼꺼 넣음
                    dis = new DataInputStream(socket.getInputStream());// input에 받을꺼 넣어짐

                    dos.writeUTF("안드로이드에서 서버로 연결요청");
                    dos.writeUTF("guswns2811@naver.com");

                } catch (IOException e) {
                    e.printStackTrace();
                    Log.w("버퍼", "버퍼생성 잘못됨");
                }
                Log.w("버퍼", "버퍼생성 잘됨");

                while (true) {
                    // 서버에서 받아옴
                    try {
                        String line = "";
                        int line2;
                        int trash = 0;
                        int truedata = 0;
                        while (true) {
                            line = dis.readUTF();
                            line2 = dis.read();
                            if (line2 == 0) {
                                trash = line2;
                            } else if (line2 >= 1) {
                                truedata = line2;

                                switch (truedata) {
                                    case 1:
                                        tts.speak("자전거입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 2:
                                        tts.speak("버스입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 3:
                                        tts.speak("자동차입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 4:
                                        tts.speak("캐리어입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 5:
                                        tts.speak("고양이입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 6:
                                        tts.speak("강아지입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 7:
                                        tts.speak("오토바이입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 8:
                                        tts.speak("간판입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 9:
                                        tts.speak("사람입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 10:
                                        tts.speak("스쿠터입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 11:
                                        tts.speak("트럭입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 12:
                                        tts.speak("휠체어입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 13:
                                        tts.speak("보호벽입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        break;
                                    case 14:
                                        tts.speak("벤치입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 15:
                                        tts.speak("볼라드입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 16:
                                        tts.speak("의자입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 17:
                                        tts.speak("소화전입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 18:
                                        tts.speak("키오스크입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 19:
                                        tts.speak("주차자동판매기입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 20:
                                        tts.speak("막대기입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 22:
                                        tts.speak("화분입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 23:
                                        tts.speak("정지신호판입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 24:
                                        tts.speak("테이블입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 25:
                                    case 26:
                                        tts.speak("신호등입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    case 27:
                                        tts.speak("나무입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        toneGenerator.startTone(ToneGenerator.TONE_DTMF_P, 1000);
                                        break;
                                    default:
                                        break;
                                }
                            }


                            if (truedata > 0) {
                                Log.w("젯슨 탐지 값 ", "" + line2);
                                data.setConnectdata(line2);
                                dos.writeUTF("하나 받았습니다. : " + line2);
                                dos.flush();
                            }
                            resultText.setText("" + truedata);
                            Log.w("서버 응답 신호string ", "" + line);
                            Log.w("서버 응답 신호1 ", "" + trash);
                            Log.w("서버 응답 신호2 ", "" + truedata);
                        }
                    } catch (Exception e) {
                    }
                }
            }
        };
        // 소켓 접속 시도, 버퍼생성
        checkUpdate.start();
    }

    void connect2() {
        data.setOnoff(0);
        mHandler = new Handler();
        Log.w("connect", "연결 하는중");
        // 받아오는거
        Thread checkUpdate = new Thread() {
            public void run() {
                String a = getport2.getText().toString();
                int b = Integer.parseInt(a);
                Log.d(TAG, "run: " + b);
                // 서버 접속
                try {
                    socket2 = new Socket(ip2, b);
                    tts.speak("서버2와 접속되었습니다", TextToSpeech.QUEUE_FLUSH, null);
                    Log.w("서버2 접속됨", "서버 접속됨");
                } catch (IOException e1) {
                    tts.speak("서버2와 접속하지 못했습니다", TextToSpeech.QUEUE_FLUSH, null);
                    Log.w("서버2접속못함", "서버접속못함");
                    e1.printStackTrace();
                }

                try {
                    dos2 = new DataOutputStream(socket2.getOutputStream());   // output에 보낼꺼 넣음
                    dis2 = new DataInputStream(socket2.getInputStream());     // input에 받을꺼 넣어짐
                    dos2.writeUTF("안드로이드 서버2 연결요청");

                } catch (IOException e) {
                    e.printStackTrace();
                    Log.w("버퍼", "버퍼생성 잘못됨");
                }
                Log.w("버퍼", "버퍼생성 잘됨");

                while (true) {
                    // 서버에서 받아옴
                    try {
                        tsdos = new DataOutputStream(socket2.getOutputStream());
                        tsdos.writeUTF("테스트전송");

                        String line = "";
                        int line2;
                        int trash = 0;
                        int truedata = 0;
                        while (true) {
                            line = dis2.readUTF();
                            line2 = dis2.read();

                            if (data.getOnoff() == 1) {
                                tsdos = new DataOutputStream(socket2.getOutputStream());
                                tsdos.writeUTF("종료");
                            }

                            if (line2 == 0) {
                                trash = line2;
                            } else if (line2 >= 1) {
                                truedata = line2;

                                switch (truedata) {
                                    case 1:
                                        tts.speak("위험구역입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        break;
                                    case 2:
                                        tts.speak("횡단보도입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        break;
                                    case 3:
                                        tts.speak("점자블록입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        break;
                                    case 4:
                                        tts.speak("차도입니다", TextToSpeech.QUEUE_FLUSH, null);
                                        break;
                                }
                            }


                            if (truedata > 0) {
                                Log.w("젯슨 탐지 값 ", "" + line2);
                                data.setConnectdata(line2);
                                dos2.writeUTF("하나 받았습니다. : " + line2);

                            }
                            if (line2 == 99) {
                                Log.w("서버에서 받아온 값 99", "" + line2);
                                socket2.close();
                                break;
                            }
                            resultText2.setText(""+truedata);
                            Log.w("서버2 응답 신호string ", "" + line);
                            Log.w("서버2 응답 신호1 ", "" + trash);
                            Log.w("서버2 응답 신호2 ", "" + truedata);
                        }
                    } catch (Exception e) {
                    }
                }
            }
        };
        // 소켓 접속 시도, 버퍼생성
        checkUpdate.start();
    }

    private RecognitionListener listener = new RecognitionListener() {
        @Override
        public void onReadyForSpeech(Bundle params) {

        }

        @Override
        public void onBeginningOfSpeech() {

        }

        @Override
        public void onRmsChanged(float rmsdB) {

        }

        @Override
        public void onBufferReceived(byte[] buffer) {

        }

        @Override
        public void onEndOfSpeech() {

        }

        @Override
        public void onError(int error) {

        }

        @Override
        public void onResults(Bundle results) {
            ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
            for (int i = 0; i < matches.size(); i++) {
                sttdata = sttdata + matches.get(i);
                Log.d(TAG, "onResults: " + matches.get(i));
                Log.d(TAG, "onResults: " + sttdata);
                data.setSttdata(sttdata);
            }
        }

        @Override
        public void onPartialResults(Bundle partialResults) {

        }

        @Override
        public void onEvent(int eventType, Bundle params) {

        }
    };

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // TTS 객체가 남아있다면 실행을 중지하고 메모리에서 제거한다.
        if (tts != null) {
            tts.stop();
            tts.shutdown();
            tts = null;
        }
    }
}