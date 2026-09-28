/*
 * etelemetry.c — IMU Simulator + Madgwick AHRS
 * ================================================
 * Simulates 6-DOF IMU sensor data and runs it through the
 * Madgwick AHRS filter to compute roll, pitch, yaw.
 * Outputs data as tab-delimited or NMEA $IMUDT sentences at 20 Hz.
 *
 * Compile:
 *   gcc etelemetry.c -o etelemetry -lm
 *
 * Usage:
 *   ./etelemetry            # tab-delimited output
 *   ./etelemetry --nmea     # NMEA $IMUDT sentences
 *   ./etelemetry | python telemetry_dashboard.py
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
  #include <windows.h>
  #define sleep_ms(ms) Sleep(ms)
#else
  #include <unistd.h>
  #define sleep_ms(ms) usleep((ms)*1000)
#endif

// ─── Madgwick Filter State ────────────────────────────────────────────────────
static float q0 = 1.0f, q1 = 0.0f, q2 = 0.0f, q3 = 0.0f;
static float beta = 0.1f;   // algorithm gain

// ─── Madgwick AHRS Update (6-DOF, no magnetometer) ───────────────────────────
void madgwick_update(float gx, float gy, float gz,
                     float ax, float ay, float az, float dt)
{
    float recipNorm;
    float s0, s1, s2, s3;
    float qDot1, qDot2, qDot3, qDot4;
    float _2q0, _2q1, _2q2, _2q3, _4q0, _4q1, _4q2;
    float _8q1, _8q2, q0q0, q1q1, q2q2, q3q3;

    /* Rate of change of quaternion from gyroscope */
    qDot1 = 0.5f * (-q1*gx - q2*gy - q3*gz);
    qDot2 = 0.5f * ( q0*gx + q2*gz - q3*gy);
    qDot3 = 0.5f * ( q0*gy - q1*gz + q3*gx);
    qDot4 = 0.5f * ( q0*gz + q1*gy - q2*gx);

    /* Normalise accelerometer */
    recipNorm = 1.0f / sqrtf(ax*ax + ay*ay + az*az);
    ax *= recipNorm; ay *= recipNorm; az *= recipNorm;

    _2q0 = 2.0f*q0; _2q1 = 2.0f*q1; _2q2 = 2.0f*q2; _2q3 = 2.0f*q3;
    _4q0 = 4.0f*q0; _4q1 = 4.0f*q1; _4q2 = 4.0f*q2;
    _8q1 = 8.0f*q1; _8q2 = 8.0f*q2;
    q0q0 = q0*q0; q1q1 = q1*q1; q2q2 = q2*q2; q3q3 = q3*q3;

    s0 = _4q0*q2q2 + _2q2*ax + _4q0*q1q1 - _2q1*ay;
    s1 = _4q1*q3q3 - _2q3*ax + 4.0f*(q0q0*q1) - _2q0*ay - _4q1 + _8q1*q1q1 + _8q1*q2q2 + _4q1*az;
    s2 = 4.0f*(q0q0*q2) + _2q0*ax + _4q2*q3q3 - _2q3*ay - _4q2 + _8q2*q1q1 + _8q2*q2q2 + _4q2*az;
    s3 = 4.0f*(q1q1*q3) - _2q1*ax + 4.0f*(q2q2*q3) - _2q2*ay;

    recipNorm = 1.0f / sqrtf(s0*s0 + s1*s1 + s2*s2 + s3*s3);
    s0 *= recipNorm; s1 *= recipNorm; s2 *= recipNorm; s3 *= recipNorm;

    qDot1 -= beta * s0;
    qDot2 -= beta * s1;
    qDot3 -= beta * s2;
    qDot4 -= beta * s3;

    q0 += qDot1 * dt;
    q1 += qDot2 * dt;
    q2 += qDot3 * dt;
    q3 += qDot4 * dt;

    recipNorm = 1.0f / sqrtf(q0*q0 + q1*q1 + q2*q2 + q3*q3);
    q0 *= recipNorm; q1 *= recipNorm; q2 *= recipNorm; q3 *= recipNorm;
}

// ─── Euler Angles from Quaternion ─────────────────────────────────────────────
void get_euler(float *roll, float *pitch, float *yaw) {
    *roll  = atan2f(2.0f*(q0*q1 + q2*q3), 1.0f - 2.0f*(q1*q1 + q2*q2)) * (180.0f/M_PI);
    *pitch = asinf (2.0f*(q0*q2 - q3*q1))                                * (180.0f/M_PI);
    *yaw   = atan2f(2.0f*(q0*q3 + q1*q2), 1.0f - 2.0f*(q2*q2 + q3*q3)) * (180.0f/M_PI);
}

// ─── NMEA Checksum ────────────────────────────────────────────────────────────
uint8_t nmea_checksum(const char *s) {
    uint8_t cs = 0;
    while (*s) cs ^= (uint8_t)(*s++);
    return cs;
}

// ─── IMU Simulator ────────────────────────────────────────────────────────────
typedef struct { float ax, ay, az, gx, gy, gz, t; } IMU;

static float sim_time = 0.0f;

IMU simulate_imu(float dt) {
    sim_time += dt;
    IMU imu;
    /* Smooth sinusoidal motion + gravity + noise */
    imu.ax = 0.05f * sinf(0.3f * sim_time)  + ((rand()%100-50)/5000.0f);
    imu.ay = 0.03f * cosf(0.2f * sim_time)  + ((rand()%100-50)/5000.0f);
    imu.az = 9.81f + 0.01f * sinf(sim_time) + ((rand()%100-50)/5000.0f);
    imu.gx = 0.02f * sinf(0.5f * sim_time)  + ((rand()%100-50)/50000.0f);
    imu.gy = 0.01f * cosf(0.4f * sim_time)  + ((rand()%100-50)/50000.0f);
    imu.gz = 0.005f* sinf(0.1f * sim_time)  + ((rand()%100-50)/50000.0f);
    imu.t  = sim_time;
    return imu;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
int main(int argc, char *argv[]) {
    int nmea_mode = (argc > 1 && strcmp(argv[1], "--nmea") == 0);
    float dt      = 0.05f;   /* 20 Hz */
    float roll, pitch, yaw;

    srand((unsigned)time(NULL));

    if (!nmea_mode) {
        printf("time\tax\tay\taz\tgx\tgy\tgz\troll\tpitch\tyaw\n");
        fflush(stdout);
    }

    while (1) {
        IMU imu = simulate_imu(dt);
        madgwick_update(imu.gx, imu.gy, imu.gz, imu.ax, imu.ay, imu.az, dt);
        get_euler(&roll, &pitch, &yaw);

        if (nmea_mode) {
            char body[128];
            snprintf(body, sizeof(body),
                     "IMUDT,%.2f,%.2f,%.2f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f",
                     roll, pitch, yaw,
                     imu.ax, imu.ay, imu.az,
                     imu.gx, imu.gy, imu.gz);
            printf("$%s*%02X\r\n", body, nmea_checksum(body));
        } else {
            printf("%.3f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.4f\t%.2f\t%.2f\t%.2f\n",
                   imu.t, imu.ax, imu.ay, imu.az,
                   imu.gx, imu.gy, imu.gz, roll, pitch, yaw);
        }
        fflush(stdout);
        sleep_ms((int)(dt * 1000));
    }
    return 0;
}
