package com.example.visualhelper;

public class Data {
    int connectdata;
    String sttdata;
    int tempdata = 0;
    double lon = 0;
    double lat = 0;
    int onoff = 0;

    public double getLon() {
        return lon;
    }

    public void setLon(double lon) {
        this.lon = lon;
    }

    public double getLat() {
        return lat;
    }

    public void setLat(double lat) {
        this.lat = lat;
    }

    public int getOnoff() {
        return onoff;
    }

    public void setOnoff(int onoff) {
        this.onoff = onoff;
    }

    public int getConnectdata() {
        return connectdata;
    }
    public void setConnectdata(int connectdata) {
        this.connectdata = connectdata;
    }

    public String getSttdata() {
        return sttdata;
    }

    public void setSttdata(String sttdata) {
        this.sttdata = sttdata;
    }

    @Override
    public String toString() {
        return "Data{" +
                "sttdata='" + sttdata + '\'' +
                '}';
    }

    public int getTempdata() {
        return tempdata;
    }

    public void setTempdata(int tempdata) {
        this.tempdata = tempdata;
    }
}
