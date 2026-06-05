from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, schemas
from io import BytesIO
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List

router = APIRouter(prefix="/api", tags=["weights"])

@router.get("/cats/{cat_id}/weights", response_model=list[schemas.WeightRecord])
def get_weights(cat_id: int, db: Session = Depends(get_db)):
    """获取猫咪的体重记录列表"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    return db.query(models.WeightRecord).filter(
        models.WeightRecord.cat_id == cat_id
    ).order_by(models.WeightRecord.date).all()

@router.post("/cats/{cat_id}/weights", response_model=schemas.WeightRecord)
def add_weight(cat_id: int, weight: schemas.WeightRecordCreate, db: Session = Depends(get_db)):
    """添加体重记录"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    new_weight = models.WeightRecord(**weight.model_dump(), cat_id=cat_id)
    db.add(new_weight)
    db.commit()
    db.refresh(new_weight)
    return new_weight

# 注意：/weights/chart 必须在 /weights/{weight_id} 之前定义，否则会被路径参数匹配
@router.get("/weights/chart")
def get_chart_data(user_id: int, db: Session = Depends(get_db)):
    """获取用户的猫咪体重图表数据"""
    cats = db.query(models.Cat).filter(models.Cat.owner_id == user_id).all()
    result = []
    for cat in cats:
        weights = db.query(models.WeightRecord).filter(
            models.WeightRecord.cat_id == cat.id
        ).order_by(models.WeightRecord.date).all()
        result.append({
            "cat_id": cat.id,
            "cat_name": cat.name,
            "data": [{"date": str(w.date), "weight": w.weight} for w in weights]
        })
    return result

@router.get("/weights/{weight_id}", response_model=schemas.WeightRecord)
def get_weight(weight_id: int, db: Session = Depends(get_db)):
    """获取单条体重记录"""
    weight = db.query(models.WeightRecord).filter(models.WeightRecord.id == weight_id).first()
    if not weight:
        raise HTTPException(status_code=404, detail="体重记录不存在")
    return weight

@router.put("/weights/{weight_id}", response_model=schemas.WeightRecord)
def update_weight(weight_id: int, weight_update: schemas.WeightRecordUpdate, db: Session = Depends(get_db)):
    """更新体重记录"""
    weight = db.query(models.WeightRecord).filter(models.WeightRecord.id == weight_id).first()
    if not weight:
        raise HTTPException(status_code=404, detail="体重记录不存在")
    update_data = weight_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(weight, key, value)
    db.commit()
    db.refresh(weight)
    return weight

@router.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db)):
    """删除体重记录"""
    weight = db.query(models.WeightRecord).filter(models.WeightRecord.id == weight_id).first()
    if not weight:
        raise HTTPException(status_code=404, detail="体重记录不存在")
    db.delete(weight)
    db.commit()
    return {"message": "删除成功"}


# ==================== 统计分析功能 ====================

@router.get("/cats/{cat_id}/weights/stats")
def get_weight_stats(
    cat_id: int,
    days: int = Query(30, description="统计最近N天的数据，默认30天"),
    db: Session = Depends(get_db)
):
    """获取猫咪体重统计数据

    返回：
    - avg_weight: 平均体重（克）
    - max_weight: 最大体重（克）
    - min_weight: 最小体重（克）
    - latest_weight: 最新体重（克）
    - weight_change: 体重变化（最新 - 最早，克）
    - trend: 趋势（上升/下降/稳定）
    - record_count: 记录数量
    - date_range: 日期范围
    """
    # 验证猫咪存在
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")

    # 计算日期范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    # 查询指定时间范围内的体重记录
    weights = db.query(models.WeightRecord).filter(
        models.WeightRecord.cat_id == cat_id,
        models.WeightRecord.date >= start_date,
        models.WeightRecord.date <= end_date
    ).order_by(models.WeightRecord.date).all()

    if not weights:
        return {
            "cat_id": cat_id,
            "cat_name": cat.name,
            "message": "该时间段内没有体重记录",
            "record_count": 0
        }

    # 计算统计数据
    weight_values = [w.weight for w in weights]
    avg_weight = sum(weight_values) / len(weight_values)
    max_weight = max(weight_values)
    min_weight = min(weight_values)
    latest_weight = weights[-1].weight
    earliest_weight = weights[0].weight
    weight_change = latest_weight - earliest_weight

    # 判断趋势（变化超过5%才算明显趋势）
    if earliest_weight > 0:
        change_percent = abs(weight_change / earliest_weight) * 100
        if change_percent < 5:
            trend = "stable"
            trend_text = "稳定"
        elif weight_change > 0:
            trend = "up"
            trend_text = "上升"
        else:
            trend = "down"
            trend_text = "下降"
    else:
        trend = "unknown"
        trend_text = "未知"

    return {
        "cat_id": cat_id,
        "cat_name": cat.name,
        "avg_weight": round(avg_weight, 1),
        "max_weight": max_weight,
        "min_weight": min_weight,
        "latest_weight": latest_weight,
        "weight_change": round(weight_change, 1),
        "change_percent": round(change_percent, 1) if earliest_weight > 0 else 0,
        "trend": trend,
        "trend_text": trend_text,
        "record_count": len(weights),
        "date_range": {
            "start": str(weights[0].date),
            "end": str(weights[-1].date)
        },
        "period_days": days
    }


@router.get("/cats/{cat_id}/weights/trend")
def get_weight_trend(
    cat_id: int,
    months: int = Query(3, description="统计最近N个月的趋势，默认3个月"),
    db: Session = Depends(get_db)
):
    """获取猫咪体重趋势数据（按周聚合）

    用于绘制趋势图，返回每周的平均体重
    """
    # 验证猫咪存在
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")

    # 计算日期范围
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=months * 30)

    # 查询体重记录
    weights = db.query(models.WeightRecord).filter(
        models.WeightRecord.cat_id == cat_id,
        models.WeightRecord.date >= start_date,
        models.WeightRecord.date <= end_date
    ).order_by(models.WeightRecord.date).all()

    if not weights:
        return {
            "cat_id": cat_id,
            "cat_name": cat.name,
            "message": "该时间段内没有体重记录",
            "weekly_data": []
        }

    # 按周聚合数据
    from collections import defaultdict
    weekly_data = defaultdict(list)

    for w in weights:
        # 计算该日期所在的周（使用 ISO 周）
        year, week_num, _ = w.date.isocalendar()
        week_key = f"{year}-W{week_num:02d}"
        weekly_data[week_key].append(w.weight)

    # 计算每周平均体重
    result = []
    for week_key in sorted(weekly_data.keys()):
        weights_in_week = weekly_data[week_key]
        avg_weight = sum(weights_in_week) / len(weights_in_week)
        result.append({
            "week": week_key,
            "avg_weight": round(avg_weight, 1),
            "record_count": len(weights_in_week)
        })

    return {
        "cat_id": cat_id,
        "cat_name": cat.name,
        "period_months": months,
        "weekly_data": result
    }


# ==================== 导入导出功能 ====================

@router.get("/weights/template")
def download_template(user_id: int, db: Session = Depends(get_db)):
    """下载体重数据导入模板"""
    # 获取用户的所有猫咪
    cats = db.query(models.Cat).filter(models.Cat.owner_id == user_id).all()

    # 创建模板数据
    data = {"日期": []}
    for cat in cats:
        data[cat.name] = []

    # 添加示例数据行
    today = datetime.now().date()
    data["日期"] = [
        (today.replace(day=1)).strftime("%Y-%m-%d"),
        (today.replace(day=15)).strftime("%Y-%m-%d"),
    ]
    for cat in cats:
        data[cat.name] = ["", ""]  # 空示例数据

    # 创建 DataFrame
    df = pd.DataFrame(data)

    # 导出到 Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='体重记录')
    output.seek(0)

    # 返回文件流
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=weight_template.xlsx"}
    )


@router.post("/weights/import")
async def import_weights(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """导入体重数据 Excel 文件"""
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传 Excel 文件 (.xlsx 或 .xls)")

    # 获取用户的所有猫咪，建立名称到ID的映射
    cats = db.query(models.Cat).filter(models.Cat.owner_id == user_id).all()
    cat_name_to_id = {cat.name: cat.id for cat in cats}

    if not cats:
        raise HTTPException(status_code=400, detail="您还没有添加任何猫咪，请先添加猫咪")

    try:
        # 读取 Excel 文件
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents), engine='openpyxl')

        if df.empty:
            raise HTTPException(status_code=400, detail="Excel 文件为空")

        # 智能识别列：第一列是日期，其他列是猫咪名称
        columns = df.columns.tolist()

        # 找到日期列（通常是第一列，或者包含"日期"字样的列）
        date_column = None
        for col in columns:
            if '日期' in str(col) or 'date' in str(col).lower():
                date_column = col
                break

        if date_column is None:
            date_column = columns[0]  # 默认第一列为日期

        # 获取猫咪列（排除日期列）
        cat_columns = [col for col in columns if col != date_column]

        # 匹配猫咪名称
        matched_cats = {}
        unmatched_columns = []

        for col in cat_columns:
            col_str = str(col).strip()
            if col_str in cat_name_to_id:
                matched_cats[col] = cat_name_to_id[col_str]
            else:
                # 尝试模糊匹配
                for cat_name, cat_id in cat_name_to_id.items():
                    if cat_name in col_str or col_str in cat_name:
                        matched_cats[col] = cat_id
                        break
                else:
                    unmatched_columns.append(col_str)

        if not matched_cats:
            raise HTTPException(
                status_code=400,
                detail=f"未能匹配到任何猫咪。您的猫咪: {list(cat_name_to_id.keys())}, Excel中的列: {cat_columns}"
            )

        # 导入数据
        imported_count = 0
        skipped_count = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                # 解析日期
                date_value = row[date_column]
                if pd.isna(date_value):
                    continue

                # 处理不同格式的日期
                if isinstance(date_value, str):
                    try:
                        record_date = datetime.strptime(date_value.strip(), "%Y-%m-%d").date()
                    except ValueError:
                        try:
                            record_date = datetime.strptime(date_value.strip(), "%Y/%m/%d").date()
                        except ValueError:
                            errors.append(f"第{idx+2}行: 无法解析日期 '{date_value}'")
                            continue
                elif isinstance(date_value, datetime):
                    record_date = date_value.date()
                else:
                    errors.append(f"第{idx+2}行: 无效的日期格式")
                    continue

                # 为每个匹配的猫咪添加体重记录
                for col, cat_id in matched_cats.items():
                    weight_value = row[col]

                    if pd.isna(weight_value) or weight_value == '':
                        continue

                    try:
                        weight = float(weight_value)
                        if weight <= 0:
                            continue

                        # 检查是否已存在该日期的记录
                        existing = db.query(models.WeightRecord).filter(
                            models.WeightRecord.cat_id == cat_id,
                            models.WeightRecord.date == record_date
                        ).first()

                        if existing:
                            # 更新现有记录
                            existing.weight = weight
                            skipped_count += 1
                        else:
                            # 创建新记录
                            new_weight = models.WeightRecord(
                                cat_id=cat_id,
                                date=record_date,
                                weight=weight
                            )
                            db.add(new_weight)
                            imported_count += 1

                    except (ValueError, TypeError):
                        errors.append(f"第{idx+2}行, 猫咪'{col}': 无效的体重值 '{weight_value}'")

            except Exception as e:
                errors.append(f"第{idx+2}行: {str(e)}")

        db.commit()

        result = {
            "success": True,
            "message": f"导入完成！新增 {imported_count} 条记录，更新 {skipped_count} 条已存在的记录",
            "imported_count": imported_count,
            "updated_count": skipped_count,
            "matched_cats": list(matched_cats.keys()),
            "unmatched_columns": unmatched_columns
        }

        if errors:
            result["errors"] = errors[:10]  # 最多返回10条错误信息
            result["error_count"] = len(errors)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/weights/export")
def export_weights(
    user_id: int,
    cat_ids: Optional[str] = Query(None, description="逗号分隔的猫咪ID列表，不传则导出所有"),
    db: Session = Depends(get_db)
):
    """导出体重数据到 Excel"""
    # 获取用户的猫咪
    query = db.query(models.Cat).filter(models.Cat.owner_id == user_id)

    if cat_ids:
        # 筛选指定猫咪
        id_list = [int(id.strip()) for id in cat_ids.split(',') if id.strip().isdigit()]
        query = query.filter(models.Cat.id.in_(id_list))

    cats = query.all()

    if not cats:
        raise HTTPException(status_code=400, detail="没有找到任何猫咪")

    # 收集所有体重数据
    all_dates = set()
    cat_weights = {}

    for cat in cats:
        weights = db.query(models.WeightRecord).filter(
            models.WeightRecord.cat_id == cat.id
        ).order_by(models.WeightRecord.date).all()

        cat_weights[cat.name] = {}
        for w in weights:
            date_str = str(w.date)
            all_dates.add(date_str)
            cat_weights[cat.name][date_str] = w.weight

    if not all_dates:
        raise HTTPException(status_code=400, detail="没有任何体重记录")

    # 按日期排序
    sorted_dates = sorted(all_dates)

    # 构建 DataFrame
    data = {"日期": sorted_dates}
    for cat in cats:
        data[cat.name] = [cat_weights[cat.name].get(date, "") for date in sorted_dates]

    df = pd.DataFrame(data)

    # 导出到 Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='体重记录')

        # 调整列宽
        worksheet = writer.sheets['体重记录']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).str.len().max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 30)

    output.seek(0)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"weight_export_{timestamp}.xlsx"

    # 返回文件流
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
