package com.workout.watch;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.widget.*;
import android.text.InputType;
import org.json.JSONArray;
import org.json.JSONObject;
import java.net.HttpURLConnection;
import java.net.URL;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;

/** Native Wear OS workout tracker, connecting directly to the same HTTPS API as the PWA. */
public class MainActivity extends Activity {
    private LinearLayout root; private TextView status;
    private SharedPreferences prefs; private JSONObject state;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private String date, session="", chosenId=""; private int restSeconds=90; private long restEnd=0; private int timerGeneration=0;
    private final String[] IDs={"A","B","C","D","E"};
    private final String[] NAMES={"가슴","광배","하체","어깨","승모"};
    private final Map<String,String[]> EX_IDS=new HashMap<>();
    private final Map<String,String[]> EX_NAMES=new HashMap<>();
    private final Map<String,int[]> REST=new HashMap<>();
    @Override public void onCreate(Bundle b){super.onCreate(b);
        prefs=getSharedPreferences("settings",MODE_PRIVATE);
        EX_IDS.put("A",new String[]{"m1","m2","m3","m4","m5","m6","m7","m8"});
        EX_NAMES.put("A",new String[]{"벤치프레스","인클라인 덤벨 프레스","체스트 플라이","딥스","머신 숄더 프레스","사이드 레터럴 레이즈","오버헤드 익스텐션","케이블 푸시다운"});
        EX_IDS.put("B",new String[]{"t1","t2","t3","t4","t5","t6","t7","t8"});
        EX_NAMES.put("B",new String[]{"하이로우","풀오버 머신","랫풀다운","체스트 서포티드 티바로우","다이스키","리버스 펙덱 플라이","해머컬","프리처컬"});
        EX_IDS.put("C",new String[]{"w1","w2","w3","w4","w5","w6","w7","w8","w9"});
        EX_NAMES.put("C",new String[]{"이너 타이","아웃 타이","불가리안 스플릿 스쿼트","핵스쿼트","덤벨 스티프 레그 데드리프트","레그 익스텐션","크런치","레그레이즈","사이드 크런치"});
        EX_IDS.put("D",new String[]{"f1","f2","f3","f4","f5","f6","f7"});
        EX_NAMES.put("D",new String[]{"덤벨 숄더 프레스","스미스 비하인드 넥 프레스","사이드 레터럴 레이즈","플라이 머신","딥스","라잉 트라이셉스 익스텐션","케이블 푸시다운"});
        EX_IDS.put("E",new String[]{"s1","s2","s3","s4","s5","s6","s7","s8","s9"});
        EX_NAMES.put("E",new String[]{"체스트 서포티드 티바로우","투암 하이로우","로우로우","암풀다운","롱풀","페이스풀","리버스 리어델트 플라이","덤벨컬","케이블 해머컬"});
        date=new SimpleDateFormat("yyyy-MM-dd",Locale.KOREA).format(new Date());
        showHome();
    }
    private void base(String title){
        timerGeneration++; // invalidate callbacks from a previous screen
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(Color.rgb(13,17,24));
        root=new LinearLayout(this);root.setOrientation(1);root.setPadding(26,18,26,24);root.setGravity(Gravity.CENTER_HORIZONTAL);
        scroll.addView(root);setContentView(scroll);
        TextView h=text(title,19);h.setGravity(Gravity.CENTER);root.addView(h);
        status=text("",12);status.setTextColor(Color.LTGRAY);root.addView(status);
    }
    private TextView text(String s,int size){TextView t=new TextView(this);t.setText(s);t.setTextColor(Color.WHITE);t.setTextSize(size);t.setPadding(3,7,3,7);return t;}
    private Button button(String s,Runnable onClick){Button b=new Button(this);b.setAllCaps(false);b.setText(s);b.setTextSize(13);b.setOnClickListener(v->onClick.run());root.addView(b);return b;}
    private EditText field(String hint,String val,boolean numeric){EditText e=new EditText(this);e.setSingleLine(true);e.setHint(hint);e.setText(val);e.setTextSize(15);e.setTextColor(Color.WHITE);e.setHintTextColor(Color.GRAY);
        e.setInputType(numeric?InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL|InputType.TYPE_NUMBER_FLAG_SIGNED:InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD);
        root.addView(e);return e;}
    private boolean configured(){return prefs.getString("url","").startsWith("https://")&&prefs.getString("token","").length()>=24;}
    private void showHome(){base("운동일지 · "+date);
        if(!configured()){status.setText("먼저 서버를 연결하세요");button("서버 연결 설정",this::showSettings);return;}
        button("↻ 기록 새로고침",this::refresh);
        button("서버 설정",this::showSettings);
        if(state==null){refresh();return;}
        JSONObject days=state.optJSONObject("days");JSONObject day=days==null?null:days.optJSONObject(date);
        session=day==null?"":day.optString("session","");
        if(!Arrays.asList(IDs).contains(session)){status.setText("오늘의 세션을 선택하세요");for(int i=0;i<IDs.length;i++){
            final String id=IDs[i];button(NAMES[i],()->selectSession(id));}return;}
        status.setText("오늘: "+label(session));
        JSONObject routine=state.optJSONObject("routine");JSONArray rSessions=routine==null?null:routine.optJSONArray("sessions");
        JSONArray exercises=null;if(rSessions!=null)for(int i=0;i<rSessions.length();i++){JSONObject s=rSessions.optJSONObject(i);if(s!=null&&session.equals(s.optString("id"))){exercises=s.optJSONArray("ex");break;}}
        if(exercises!=null){for(int i=0;i<exercises.length();i++){JSONObject ex=exercises.optJSONObject(i);if(ex==null||ex.optBoolean("del",false))continue;
            String id=ex.optString("id"),name=ex.optString("n");int rest=ex.optInt("rest",90);
            button(name,()->showExercise(id,name,rest));}}
        else {String[] ids=EX_IDS.get(session),names=EX_NAMES.get(session);
            for(int i=0;i<ids.length;i++){final String id=ids[i],name=names[i];button(name,()->showExercise(id,name,90));}}
    }
    private String label(String id){for(int i=0;i<IDs.length;i++)if(IDs[i].equals(id))return NAMES[i];return id;}
    private void showSettings(){base("동기화 서버 설정");status.setText("휴대폰 웹앱과 동일한 서버·토큰을 입력하세요");
        EditText url=field("HTTPS 서버 URL",prefs.getString("url",""),false);
        EditText token=field("토큰",prefs.getString("token",""),false);
        button("저장하고 연결",()->{String u=url.getText().toString().trim().replaceAll("/+$","");String t=token.getText().toString().trim();
            if(!u.startsWith("https://")||t.length()<24){status.setText("HTTPS URL 및 24자 이상 토큰이 필요합니다");return;}
            prefs.edit().putString("url",u).putString("token",t).apply();state=null;showHome();});
        button("뒤로",this::showHome);
    }
    private void refresh(){request("GET","/api/state",null,(j)->{state=j;showHome();});}
    private void selectSession(String id){JSONObject o=new JSONObject();try{o.put("date",date);o.put("session",id);}catch(Exception ignored){}
        request("POST","/api/watch/session",o,j->refresh());}
    private void showExercise(String id,String name,int rest){chosenId=id;restSeconds=rest;base(name);button("← 운동 목록",this::showHome);
        JSONObject days=state.optJSONObject("days"),day=days==null?null:days.optJSONObject(date);
        JSONObject sets=day==null?null:day.optJSONObject("sets");JSONArray entries=sets==null?null:sets.optJSONArray(id);
        int index=entries==null?0:entries.length();
        String kg="",reps="";if(index>0){JSONObject prev=entries.optJSONObject(index-1);if(prev!=null){kg=prev.optString("kg","");reps=prev.optString("reps","");}}
        status.setText("완료 "+index+"세트");
        EditText kgInput=field("중량 (kg)",kg,true);EditText repsInput=field("반복 횟수",reps,true);
        final int next=index;
        button("세트 저장 + 휴식 시작",()->saveSet(id,name,next,kgInput,repsInput,rest));
        if(index>0){final int last=index-1;button("마지막 세트 수정",()->saveSet(id,name,last,kgInput,repsInput,rest));}
        button("종목 완료",()->{JSONObject x=new JSONObject();try{x.put("date",date);x.put("exercise_id",id);x.put("index",0);x.put("kg",0);x.put("reps",0);}catch(Exception ignored){}
            request("POST","/api/watch/check",x,j->refresh());});
        button("기록 새로고침",()->request("GET","/api/state",null,j->{state=j;showExercise(id,name,rest);}));
    }
    private void saveSet(String id,String name,int i,EditText kgInput,EditText repsInput,int rest){
        double kg;int reps;try{kg=Double.parseDouble(kgInput.getText().toString());reps=Integer.parseInt(repsInput.getText().toString());
            if(kg<0||reps<=0)throw new Exception();}catch(Exception e){status.setText("중량과 반복 횟수를 확인하세요");return;}
        JSONObject o=new JSONObject();try{o.put("date",date);o.put("exercise_id",id);o.put("index",i);o.put("kg",kg);o.put("reps",reps);}catch(Exception ignored){}
        request("POST","/api/watch/set",o,j->{restEnd=System.currentTimeMillis()+rest*1000L;showRest(name,id,rest);});
    }
    private void showRest(String name,String id,int rest){base("세트 저장 완료");TextView count=text("휴식",25);root.addView(count);
        final int generation=timerGeneration;
        final Runnable[] tick={null};tick[0]=()->{if(generation!=timerGeneration||!id.equals(chosenId))return;long remain=Math.max(0,(restEnd-System.currentTimeMillis()+999)/1000);
            count.setText(String.format(Locale.KOREA,"휴식 %d:%02d",remain/60,remain%60));
            if(remain>0)handler.postDelayed(tick[0],1000);else{count.setText("휴식 종료 ✓");}};
        tick[0].run();
        button("+15초",()->{restEnd+=15000;});button("−15초",()->{restEnd-=15000;});
        button("다음 세트",()->{chosenId="";request("GET","/api/state",null,j->{state=j;showExercise(id,name,rest);});});
        button("운동 목록",()->{chosenId="";refresh();});
    }
    interface Done {void success(JSONObject data);}
    private void request(String method,String path,JSONObject payload,Done done){
        String base=prefs.getString("url",""),token=prefs.getString("token","");
        new Thread(()->{try{
            HttpURLConnection c=(HttpURLConnection)new URL(base+path).openConnection();c.setConnectTimeout(12000);c.setReadTimeout(12000);
            c.setRequestMethod(method);c.setRequestProperty("Authorization","Bearer "+token);
            if(payload!=null){c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json; charset=utf-8");
                try(OutputStream out=c.getOutputStream()){out.write(payload.toString().getBytes(StandardCharsets.UTF_8));}}
            int code=c.getResponseCode();InputStream stream=code<400?c.getInputStream():c.getErrorStream();
            String data;try(stream){ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int n;while((n=stream.read(buffer))!=-1)bytes.write(buffer,0,n);data=bytes.toString("UTF-8");}
            if(code>=400)throw new Exception("서버 오류 "+code+": "+data);
            JSONObject result=new JSONObject(data);runOnUiThread(()->done.success(result));
            c.disconnect();
        }catch(Exception e){runOnUiThread(()->{if(status!=null)status.setText("연결 실패: "+e.getMessage());});}}).start();
    }
}
