#pragma once
#include "rednose/helpers/ekf.h"
extern "C" {
void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea);
void car_err_fun(double *nom_x, double *delta_x, double *out_2544164363282967113);
void car_inv_err_fun(double *nom_x, double *true_x, double *out_8399920200457521258);
void car_H_mod_fun(double *state, double *out_2795865099041046181);
void car_f_fun(double *state, double dt, double *out_8734319020564926158);
void car_F_fun(double *state, double dt, double *out_8208332734087594077);
void car_h_25(double *state, double *unused, double *out_3651263878388926264);
void car_H_25(double *state, double *unused, double *out_5125472933932813624);
void car_h_24(double *state, double *unused, double *out_8166516142223322880);
void car_H_24(double *state, double *unused, double *out_7302687357539963597);
void car_h_30(double *state, double *unused, double *out_8640032999479965223);
void car_H_30(double *state, double *unused, double *out_7643805892440062251);
void car_h_26(double *state, double *unused, double *out_5616905775409113113);
void car_H_26(double *state, double *unused, double *out_1383969615058757400);
void car_h_27(double *state, double *unused, double *out_1311116119292366968);
void car_H_27(double *state, double *unused, double *out_8579344110085546148);
void car_h_29(double *state, double *unused, double *out_7202305753420888742);
void car_H_29(double *state, double *unused, double *out_8154037236754454435);
void car_h_28(double *state, double *unused, double *out_4727389408941436984);
void car_H_28(double *state, double *unused, double *out_3071638219684923861);
void car_h_31(double *state, double *unused, double *out_654870953555015104);
void car_H_31(double *state, double *unused, double *out_757761512825405924);
void car_predict(double *in_x, double *in_P, double *in_Q, double dt);
void car_set_mass(double x);
void car_set_rotational_inertia(double x);
void car_set_center_to_front(double x);
void car_set_center_to_rear(double x);
void car_set_stiffness_front(double x);
void car_set_stiffness_rear(double x);
}